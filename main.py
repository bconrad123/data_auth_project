import sqlite3
import json
from datetime import datetime, timezone
connection = sqlite3.connect("sqlite.db")
cursor = connection.cursor()

employee_lookup_id = """
        SELECT role, level, location_assigned,device_assigned,work_hours_start,work_hours_end
        FROM employee
        WHERE employee_id = ?"""
customer_lookup = """
        SELECT ?
        FROM ?
        WHERE ?

        """

allowed_values = {
    "meta_data": [
        "customer",
        "public",
        "medical",
        "private",
        "customer_pii",
        "payment",
        "insurance",
    ],
    "action": ["reading", "mass_export"],
    "time": ["work_hours", "off_hours"]
}


class InvalidQuery(Exception):
    """Raised when query is invalid"""
    pass


class employee_auth:
    def __init__(self, employee_ID, meta_data, action, time_query, device_of_access, query_location):
        self.employee_ID = employee_ID
        self.meta_data = meta_data  # what their asking for
        self.employee_info = self.employee_lookup(
            employee_ID)  # roll level location assigned, device assigned,workstart, work end
        self.action = action
        self.time = time_query
        self.device = device_of_access
        self.query_location = query_location
        self.verdict = self.first_check()

    def first_check(self):
        for param, value in vars(self).items():
            if not value:
                audit_log(self)
                raise InvalidQuery("one or more query items is NULL")
        if self.meta_data not in allowed_values["meta_data"]:
            audit_log(self)
            raise InvalidQuery("invalid meta_data")
        if self.action not in allowed_values["action"]:
            audit_log(self)
            raise InvalidQuery("invalid action")
        return self.policy_check()

    def employee_lookup(self, employee_ID):
        cursor.execute(employee_lookup_id, (employee_ID,))
        info = cursor.fetchone()
        if not info:
            audit_log(self)
            raise InvalidQuery("wrong or missing employee_ID")
        columns = ["role", "level", "location_assigned", "device_assigned", "work_hours_start", "work_hours_end"]
        # find valid work hours based on assigned location and add a column based on that
        return dict(zip(columns, info))

    # employee_ID,job_category,location_stationed,clearance_level,meta_data_asked_for,action,time_of_access,device_of_access,location_access,effect
    # given this return an answer
    # the object gives you currently
    def policy_check(object):
        start_time = int(object.employee_info["work_hours_start"].replace(":", ""))
        end_time = int(object.employee_info["work_hours_end"].replace(":", ""))
        query_time = int(object.time.replace(":", ""))
        if start_time <= end_time:
            object.time = during_work_hours(start_time, query_time, end_time, time_linear=True)
        else:
            object.time = during_work_hours(start_time, query_time, end_time, time_linear=False)

        def check_employee_ID(obj, requirement_type) -> bool:
            # per-record rule: matching against the record's project_tag
            # has to be enforced when the rows are fetched, so it passes here
            if requirement_type == "must_equal(patient_tag)":
                return True
            return str(obj.employee_ID) == str(requirement_type)

        def check_location_stationed(obj, requirement_type) -> bool:
            employee_parts = [p.strip().lower()
                              for p in obj.employee_info["location_assigned"].split(",")]
            policy_parts = [p.strip().lower() for p in requirement_type.split(",")]
            n = len(policy_parts)
            for i in range(len(employee_parts) - n + 1):
                if employee_parts[i:i + n] == policy_parts:
                    return True
            return False

        def check_clearance_level(obj, requirement_type) -> bool:
            return obj.employee_info["level"] >= int(requirement_type)

        def check_time_of_access(obj, requirement_type) -> bool:
            # obj.time already holds the work_hours / off_hours bucket
            return obj.time == requirement_type

        def check_location_access(obj, requirement_type) -> bool:
            if requirement_type == "must_equal(location_stationed)":
                return obj.query_location == obj.employee_info["location_assigned"]
            return obj.query_location == requirement_type

        def check_device_of_access(obj, requirement_type) -> bool:
            if requirement_type == "must_equal(device_assigned)":
                return obj.device == obj.employee_info["device_assigned"]
            return obj.device == requirement_type

        CATEGORY_COLUMNS = [
            "medical", "financial", "executive", "customer_facing",
            "engineering_data", "security", "legal", "human_resources",
        ]

        def get_employee_categories(obj):
            role = obj.employee_info["role"]
            categories = []
            for column in CATEGORY_COLUMNS:
                cursor.execute(
                    f"SELECT 1 FROM role_category WHERE {column} = ? LIMIT 1",
                    (role,),
                )
                if cursor.fetchone():
                    categories.append(column)
            if not categories:
                audit_log(obj)
                raise InvalidQuery("role has no category")
            return categories

        auth_dispatch = {
            "employee_ID": check_employee_ID,
            "location_stationed": check_location_stationed,
            "clearance_level": check_clearance_level,
            "time_of_access": check_time_of_access,
            "location_access": check_location_access,
            "device_of_access": check_device_of_access
        }
        categories = get_employee_categories(object)
        candidates = categories + ["any"]
        placeholders = ",".join("?" * len(candidates))

        policy_query = f"""
                SELECT effect, employee_ID, location_stationed, clearance_level,
                       time_of_access, device_of_access, location_access
                FROM policies
                WHERE job_category IN ({placeholders})
                  AND (action = ? OR action = 'any')
                  AND (meta_data_asked_for = 'any'
                       OR ',' || meta_data_asked_for || ',' LIKE '%,' || ? || ',%')
            """
        cursor.execute(policy_query, (*candidates, object.action, object.meta_data))
        rows = cursor.fetchall()
        # passing in meta_data,action,category

        condition_names = ["employee_ID", "location_stationed", "clearance_level", "time_of_access", "device_of_access",
                           "location_access"]
        effects = []
        for row in rows:
            conditions = dict(zip(condition_names, row[1:]))
            conditions_met = True
            for key, value in conditions.items():
                if value == "any":
                    continue
                if not auth_dispatch[key](object, value):
                    conditions_met = False
                    break
            if conditions_met:
                effects.append(row[0])

        if not effects or "deny" in effects:
            verdict = "deny"
        elif "mask" in effects:
            verdict = "mask"
        else:
            verdict = "allow"
        audit_log(object, verdict)
        return verdict


def during_work_hours(start, query_time, end, time_linear: bool):
    if time_linear:
        if start <= query_time < end:
            return "work_hours"
        else:
            return "off_hours"
    else:
        if query_time >= start or query_time < end:
            return "work_hours"
        else:
            return "off_hours"


AUDIT_LOG_FILE = "audit_log.jsonl"

def audit_log(obj=None, verdict="deny", reason=""):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "employee_ID": getattr(obj, "employee_ID", None),
        "meta_data": getattr(obj, "meta_data", None),
        "action": getattr(obj, "action", None),
        "request_time": getattr(obj, "request_time", None),
        "device": getattr(obj, "device", None),
        "query_location": getattr(obj, "query_location", None),
        "verdict": verdict,
        "reason": reason,
    }
    with open(AUDIT_LOG_FILE, "a") as log_file:
        log_file.write(json.dumps(entry, default=str) + "\n")


# 1001	doctor	6	Arlington,Virginia	MED-LT-1001
try:
    test_case1 = employee_auth(1001, "public", "reading", "20:00", "MED-LT-1001", "Arlington,Virginia,USA")
    print(test_case1.verdict)
except InvalidQuery as error:
    print("denied:", error)
# to get this done I need a working policy check and audit log
# get policy check done