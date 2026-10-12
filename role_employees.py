import sqlite3

connection = sqlite3.connect("sqlite.db")
cursor = connection.cursor()

make_employee_table = """
CREATE TABLE IF NOT EXISTS employee(
    employee_id INTEGER PRIMARY KEY,
    role TEXT,
    level INTEGER,
    location_assigned TEXT,
    device_assigned TEXT,
    work_hours_start TEXT,
    work_hours_end TEXT
)
"""
#work hours is in UTC

make_role_category_table = """
CREATE TABLE IF NOT EXISTS role_category(
    medical TEXT,
    financial TEXT,
    executive TEXT,
    customer_facing TEXT,
    engineering_data TEXT,
    security TEXT,
    legal TEXT,
    human_resources TEXT
)
"""

# 10 seed employees
insert_employees = """
INSERT INTO employee (employee_id, role, level, location_assigned, device_assigned,work_hours_start,work_hours_end)
VALUES
    (1001, 'doctor',              6, 'Arlington,Virginia,USA',  'MED-LT-1001', '13:00', '21:00'),
    (1002, 'nurse_practitioner',  5, 'Baltimore,Maryland,USA',  'MED-LT-1002', '13:00', '21:00'),
    (1003, 'customer_support',    2, 'Seattle,Washington,USA',  'SUP-LT-1003', '16:00', '00:00'),
    (1004, 'finance_engineer',    4, 'Seattle,Washington,USA',  'FIN-LT-1004', '16:00', '00:00'),
    (1005, 'benefits_specialist', 5, 'Dublin,Ireland',          'HR-LT-1005',  '08:00', '16:00'),
    (1006, 'software_engineer',   3, 'Arlington,Virginia,USA',  'ENG-LT-1006', '13:00', '21:00'),
    (1007, 'data_engineer',       4, 'Austin,Texas,USA',        'ENG-LT-1007', '14:00', '22:00'),
    (1008, 'security_analyst',    4, 'Herndon,Virginia,USA',    'SEC-LT-1008', '13:00', '21:00'),
    (1009, 'corporate_counsel',   5, 'Washington,DC,USA',       'LEG-LT-1009', '13:00', '21:00'),
    (1010, 'vp_operations',       6, 'New York,New York,USA',   'EXE-LT-1010', '13:00', '21:00')
    """
# one insert per role, filling every category that role belongs to
insert_doctor_category = """
INSERT INTO role_category (medical) VALUES ('doctor')
"""
insert_nurse_practitioner_category = """
INSERT INTO role_category (medical) VALUES ('nurse_practitioner')
"""
insert_customer_support_category = """
INSERT INTO role_category (customer_facing) VALUES ('customer_support')
"""
# belongs to two categories, so one row with both columns filled
insert_finance_engineer_category = """
INSERT INTO role_category (financial, engineering_data)
VALUES ('finance_engineer', 'finance_engineer')
"""
insert_benefits_specialist_category = """
INSERT INTO role_category (human_resources, medical)
VALUES ('benefits_specialist', 'benefits_specialist')
"""
insert_software_engineer_category = """
INSERT INTO role_category (engineering_data) VALUES ('software_engineer')
"""
insert_data_engineer_category = """
INSERT INTO role_category (engineering_data) VALUES ('data_engineer')
"""
insert_security_analyst_category = """
INSERT INTO role_category (security) VALUES ('security_analyst')
"""
insert_corporate_counsel_category = """
INSERT INTO role_category (legal) VALUES ('corporate_counsel')
"""
insert_vp_operations_category = """
INSERT INTO role_category (executive) VALUES ('vp_operations')
"""

cursor.execute(make_employee_table)
cursor.execute(make_role_category_table)

# keeps re-runs from duplicating rows or violating the primary key
cursor.execute("DELETE FROM employee")
cursor.execute("DELETE FROM role_category")

cursor.execute(insert_employees)

for category_insert in [
    insert_doctor_category,
    insert_nurse_practitioner_category,
    insert_customer_support_category,
    insert_finance_engineer_category,
    insert_benefits_specialist_category,
    insert_software_engineer_category,
    insert_data_engineer_category,
    insert_security_analyst_category,
    insert_corporate_counsel_category,
    insert_vp_operations_category,
]:
    cursor.execute(category_insert)

connection.commit()
connection.close()