import sqlite3

connection = sqlite3.connect("sqlite.db")
cursor = connection.cursor()
cursor.execute("PRAGMA foreign_keys = ON")  # SQLite ignores foreign keys unless this is on

make_customer_table = """
CREATE TABLE IF NOT EXISTS customer(
    customer_id INTEGER PRIMARY KEY,
    name TEXT,
    email_address TEXT UNIQUE,
    physical_address TEXT,
    phone_number TEXT,
    credit_card_number TEXT,
    behavioral_portfolio BLOB,
    region TEXT,
    IP_address TEXT,
    signup_date DATE DEFAULT CURRENT_DATE,
    purchase_history BLOB,
    project_tag TEXT
)
"""

make_patient_table = """
CREATE TABLE IF NOT EXISTS patient(
    customer_id INTEGER,
    patient_id INTEGER PRIMARY KEY,
    email_address TEXT,
    insurance TEXT,
    SSN TEXT,
    medical_information BLOB,
    project_tag TEXT,
    FOREIGN KEY (customer_id) REFERENCES customer(customer_id)
)
"""

# 10 seed customers. project_tag matches an employee_id from the employee table:
# 1001 doctor, 1002 nurse_practitioner, 1003 customer_support,
# 1004 finance_engineer, 1005 benefits_specialist
insert_customer = """
INSERT INTO customer (
    name, email_address, physical_address, phone_number, credit_card_number,
    behavioral_portfolio, region, IP_address, purchase_history, project_tag
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

customers = [
    ("Software Developer", "Ilovelinux@gmail.com",   "11111 Heartcrest Lane, Arlington,Virginia", "703-555-0101", "4000-0000-0000-0001", b'{"visits": 14}', "US-East",    "203.0.113.11", b'{"orders": 3}',  "1001"),
    ("Maria Alvarez",      "maria.alvarez@example.com", "220 Pine St, Seattle,Washington",        "206-555-0102", "4000-0000-0000-0002", b'{"visits": 40}', "US-West",    "203.0.113.12", b'{"orders": 9}',  "1003"),
    ("James Okafor",       "james.okafor@example.com",  "48 Lakeview Dr, Austin,Texas",           "512-555-0103", "4000-0000-0000-0003", b'{"visits": 7}',  "US-South",   "203.0.113.13", b'{"orders": 1}',  "1003"),
    ("Priya Raman",        "priya.raman@example.com",   "9 Harbor Ave, Baltimore,Maryland",       "410-555-0104", "4000-0000-0000-0004", b'{"visits": 22}', "US-East",    "203.0.113.14", b'{"orders": 5}',  "1004"),
    ("Daniel Whitfield",   "daniel.whitfield@example.com", "73 Oak Ln, Arlington,Virginia",       "703-555-0105", "4000-0000-0000-0005", b'{"visits": 18}', "US-East",    "203.0.113.15", b'{"orders": 4}',  "1001"),
    ("Hannah Cho",         "hannah.cho@example.com",    "512 Maple Ct, Baltimore,Maryland",       "410-555-0106", "4000-0000-0000-0006", b'{"visits": 31}', "US-East",    "203.0.113.16", b'{"orders": 8}',  "1002"),
    ("Marcus Bell",        "marcus.bell@example.com",   "14 River Rd, Herndon,Virginia",          "571-555-0107", "4000-0000-0000-0007", b'{"visits": 5}',  "US-East",    "203.0.113.17", b'{"orders": 2}',  "1001"),
    ("Elena Petrova",      "elena.petrova@example.com", "31 Grafton St, Dublin,Ireland",          "353-555-0108", "4000-0000-0000-0008", b'{"visits": 12}', "EU",         "203.0.113.18", b'{"orders": 6}',  "1005"),
    ("Tom Nguyen",         "tom.nguyen@example.com",    "600 5th Ave, New York,New York",         "212-555-0109", "4000-0000-0000-0009", b'{"visits": 27}', "US-East",    "203.0.113.19", b'{"orders": 11}', "1003"),
    ("Aisha Khan",         "aisha.khan@example.com",    "88 Bay St, Washington,DC",               "202-555-0110", "4000-0000-0000-0010", b'{"visits": 9}',  "US-East",    "203.0.113.20", b'{"orders": 3}',  "1002"),
]

# uses email address to get customer_id from prexisting customer and inserts into system
insert_patient = """
INSERT INTO patient (customer_id, email_address, insurance, SSN, medical_information, project_tag)
SELECT customer_id, email_address, ?, ?, ?, ?
FROM customer
WHERE email_address = ?
"""

# (insurance, SSN, medical_information, project_tag, email to look up)
patients = [
    ("MED STAR",   "900-00-0001", b'{"notes": "annual checkup"}', "1001", "Ilovelinux@gmail.com"),
    ("Aetna",      "900-00-0002", b'{"notes": "knee injury"}',    "1001", "daniel.whitfield@example.com"),
    ("Cigna",      "900-00-0003", b'{"notes": "asthma review"}',  "1002", "hannah.cho@example.com"),
    ("MED STAR",   "900-00-0004", b'{"notes": "follow-up"}',      "1001", "marcus.bell@example.com"),
    ("UnitedHealth", "900-00-0005", b'{"notes": "lab work"}',     "1002", "aisha.khan@example.com"),
]# the b prefix is to tell python the value is in bytes, the json format is just example of data

select_customer = "SELECT * FROM customer"
select_patient = "SELECT * FROM patient"

cursor.execute(make_customer_table)
cursor.execute(make_patient_table)

# keeps re-runs from duplicating rows (patient first because it references customer)
cursor.execute("DELETE FROM patient")
cursor.execute("DELETE FROM customer")

cursor.executemany(insert_customer, customers)
cursor.executemany(insert_patient, patients)

for row in cursor.execute(select_customer).fetchall():
    print(row)
for row in cursor.execute(select_patient).fetchall():
    print(row)

connection.commit()
connection.close()