#!/usr/bin/env python3
from hl7_parser import HL7Parser

# Test the basic name parsing
test_messages = [
    # Simple name
    (r"""MSH|^~\&|SYS|FAC|SYS|FAC|20250502090000||SIU^S12|MSG001|P|2.5
PID|||P001||Doe^John||19850210|M
SCH|001|^^^20250502100000^^60""", 
     "John", "Doe"),
    
    # Name with middle
    (r"""MSH|^~\&|SYS|FAC|SYS|FAC|20250502090000||SIU^S12|MSG002|P|2.5
PID|||P002||Smith^Jane^Marie||19900315|F
SCH|002|^^^20250502110000^^60""",
     "Jane", "Smith"),
    
    # Complex name
    (r"""MSH|^~\&|SYS|FAC|SYS|FAC|20250502090000||SIU^S12|MSG003|P|2.5
PID|||P003||Johnson^Robert^Lee^Jr.^Mr.||19750620|M
SCH|003|^^^20250502120000^^60""",
     "Robert", "Johnson"),
]

for i, (message, expected_first, expected_last) in enumerate(test_messages):
    print(f"\nTest {i+1}:")
    try:
        appointment = HL7Parser.parse_siu_message(message)
        print(f"  Appointment ID: {appointment.appointment_id}")
        if appointment.patient:
            print(f"  Patient: {appointment.patient.first_name} {appointment.patient.last_name}")
            print(f"  Expected: {expected_first} {expected_last}")
            print(f"  Match: {appointment.patient.first_name == expected_first and appointment.patient.last_name == expected_last}")
    except Exception as e:
        print(f"  Error: {e}")

# Test timestamp parsing
print("\n\nTimestamp parsing test:")
test_message = r"""MSH|^~\&|SYS|FAC|SYS|FAC|20250502090000||SIU^S12|MSG001|P|2.5
PID|||P001||Test^Patient||19850210|M
SCH|001|^^^20250502130000^^60"""

appointment = HL7Parser.parse_siu_message(test_message)
print(f"Appointment datetime: {appointment.appointment_datetime}")
print(f"Patient DOB: {appointment.patient.dob}")
