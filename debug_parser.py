#!/usr/bin/env python3
from hl7_parser import HL7Parser

# Test 1: Simple name parsing
print("Test 1: Simple name parsing")
hl7_message = r"""MSH|^~\&|SYSTEM_A||SYSTEM_B||20250502090000||SIU^S12|MSG002|P|2.5
PID|||P67890||Smith^Jane"""

print("Parsing message...")
try:
    appointment = HL7Parser.parse_siu_message(hl7_message)
    print(f"Appointment ID: {appointment.appointment_id}")
    if appointment.patient:
        print(f"Patient ID: {appointment.patient.id}")
        print(f"Patient Name field: '{appointment.patient.last_name}' '{appointment.patient.first_name}'")
        print(f"Raw name field: Should be 'Smith^Jane'")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*50 + "\n")

# Test 2: Complete message
print("Test 2: Complete message parsing")
hl7_message = r"""MSH|^~\&|SCHED_SYS|CLINIC_A|EHR_SYS|HOSPITAL|20250502090000||SIU^S12|MSG001|P|2.5
PID|1||P12345||Doe^John^^^Mr.||19850210|M|||123 Main St^^Springfield^IL^62701
SCH|123456|^^^20250502130000^^60|ROUTINE|^^Clinic A Room 203|^Smith^Jane^MD^D67890
PV1|1|O|OPD^203||||^Smith^Jane^MD|||REF123"""

print("Parsing message...")
try:
    appointment = HL7Parser.parse_siu_message(hl7_message)
    print(f"Appointment ID: {appointment.appointment_id}")
    print(f"Appointment Datetime: {appointment.appointment_datetime}")
    print(f"Reason: {appointment.reason}")
    print(f"Location: {appointment.location}")
    
    if appointment.patient:
        print(f"\nPatient:")
        print(f"  ID: {appointment.patient.id}")
        print(f"  Name: {appointment.patient.first_name} {appointment.patient.last_name}")
        print(f"  DOB: {appointment.patient.dob}")
        print(f"  Gender: {appointment.patient.gender}")
    
    if appointment.provider:
        print(f"\nProvider:")
        print(f"  ID: {appointment.provider.id}")
        print(f"  Name: {appointment.provider.name}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*50 + "\n")

# Test 3: Debug the parsing steps
print("Test 3: Debug internal parsing")
from hl7_parser.parser import HL7Parser as Parser

hl7_message = r"""MSH|^~\&|SYS|FAC|SYS|FAC|20250502090000||SIU^S12|MSG001|P|2.5
PID|||P001||Doe^John||19850210|M
SCH|001|^^^20250502100000^^60"""

try:
    # Parse the message
    message = Parser.parse_message(hl7_message)
    print("Parsed segments:")
    for seg_type, segments in message.segments.items():
        print(f"  {seg_type}: {segments[0] if segments else 'None'}")
    
    # Check PID segment specifically
    print("\nPID segment fields:")
    pid_fields = message.segments.get('PID', [[]])[0]
    for i, field in enumerate(pid_fields):
        print(f"  PID.{i}: '{field}'")
    
    # Check name field (PID.5)
    if len(pid_fields) > 4:
        print(f"\nName field (PID.5): '{pid_fields[4]}'")
        print(f"Split by ^: {pid_fields[4].split('^')}")
    
    # Check SCH segment
    print("\nSCH segment fields:")
    sch_fields = message.segments.get('SCH', [[]])[0]
    for i, field in enumerate(sch_fields):
        print(f"  SCH.{i}: '{field}'")
    
    # Check datetime field
    if len(sch_fields) > 2:
        print(f"\nSCH.2 field: '{sch_fields[2]}'")
        print(f"Split by ^: {sch_fields[2].split('^')}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
