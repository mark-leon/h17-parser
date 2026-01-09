"""
Unit tests for HL7 parser.
"""
import unittest
import tempfile
import os
from hl7_parser.parser import HL7Parser, HL7FileParser
from hl7_parser.exceptions import InvalidMessageError, HL7ParseError


class TestHL7Parser(unittest.TestCase):
    
    def test_valid_siu_message(self):
        """Test parsing a valid SIU message."""
        # Use raw string or escape backslash
        hl7_message = r"""MSH|^~\&|SCHED_SYS|CLINIC_A|EHR_SYS|HOSPITAL|20250502090000||SIU^S12|MSG001|P|2.5
PID|1||P12345||Doe^John^^^Mr.||19850210|M|||123 Main St^^Springfield^IL^62701
SCH|123456|^^^20250502130000^^60|ROUTINE|^^Clinic A Room 203|^Smith^Jane^MD^D67890
PV1|1|O|OPD^203||||^Smith^Jane^MD|||REF123"""
        
        appointment = HL7Parser.parse_siu_message(hl7_message)
        
        self.assertEqual(appointment.appointment_id, "123456")
        # Check datetime contains the date
        self.assertIsNotNone(appointment.appointment_datetime)
        self.assertIn("2025-05-02", appointment.appointment_datetime)
        
        self.assertEqual(appointment.reason, "ROUTINE")
        # PV1 location (203) overrides SCH location
        self.assertEqual(appointment.location, "OPD")  # PV1.3.1
        
        # Check patient
        self.assertIsNotNone(appointment.patient)
        self.assertEqual(appointment.patient.id, "P12345")
        self.assertEqual(appointment.patient.first_name, "John")
        self.assertEqual(appointment.patient.last_name, "Doe")
        self.assertIsNotNone(appointment.patient.dob)
        self.assertIn("1985-02-10", appointment.patient.dob)
        self.assertEqual(appointment.patient.gender, "M")
        
        # Check provider
        self.assertIsNotNone(appointment.provider)
        self.assertEqual(appointment.provider.id, "D67890")
        self.assertEqual(appointment.provider.name, "Jane Smith MD")
    
    def test_missing_segments(self):
        """Test parsing message with missing segments."""
        hl7_message = r"""MSH|^~\&|SYSTEM_A||SYSTEM_B||20250502090000||SIU^S12|MSG002|P|2.5
PID|||P67890||Smith^Jane"""
        # Missing SCH and PV1 segments
        
        appointment = HL7Parser.parse_siu_message(hl7_message)
        
        self.assertIsNone(appointment.appointment_id)
        self.assertIsNone(appointment.appointment_datetime)
        self.assertIsNone(appointment.location)
        self.assertIsNone(appointment.reason)
        self.assertIsNone(appointment.provider)
        
        # Patient should still be parsed
        self.assertIsNotNone(appointment.patient)
        self.assertEqual(appointment.patient.id, "P67890")
        self.assertEqual(appointment.patient.first_name, "Jane")
        self.assertEqual(appointment.patient.last_name, "Smith")
        self.assertIsNone(appointment.patient.dob)
        self.assertIsNone(appointment.patient.gender)
    
    def test_wrong_message_type(self):
        """Test parsing non-SIU message."""
        hl7_message = r"""MSH|^~\&|SYSTEM_A|FAC_A|SYSTEM_B|FAC_B|20250502090000||ADT^A01|MSG003|P|2.5"""
        
        with self.assertRaises(InvalidMessageError):
            HL7Parser.parse_siu_message(hl7_message)
    
    def test_malformed_message(self):
        """Test parsing malformed message."""
        hl7_message = """Not an HL7 message"""
        
        with self.assertRaises(InvalidMessageError):
            HL7Parser.parse_siu_message(hl7_message)
    
    def test_empty_fields(self):
        """Test parsing message with empty fields."""
        hl7_message = r"""MSH|^~\&|SYS||SYS||20250502090000||SIU^S12|MSG004|P|2.5
PID|||||||||
SCH||||||||"""
        
        appointment = HL7Parser.parse_siu_message(hl7_message)
        
        self.assertIsNone(appointment.appointment_id)
        # Patient object exists but all fields are None
        self.assertIsNotNone(appointment.patient)
        self.assertIsNone(appointment.patient.id)
        self.assertIsNone(appointment.patient.first_name)
        self.assertIsNone(appointment.patient.last_name)
        self.assertIsNone(appointment.patient.dob)
        self.assertIsNone(appointment.patient.gender)
    
    def test_timestamp_parsing(self):
        """Test various timestamp formats."""
        # Full timestamp with timezone - note: in test data, datetime is in SCH.2
        hl7_message = r"""MSH|^~\&|SYS|FAC|SYS|FAC|20250502090000||SIU^S12|MSG005|P|2.5
PID|||P001||Test^Patient||19850210|M
SCH|001|^^^20250502130000+0500^^60"""
        
        appointment = HL7Parser.parse_siu_message(hl7_message)
        # Check if datetime was parsed
        self.assertIsNotNone(appointment.appointment_datetime)
        # It should contain "2025-05-02"
        self.assertIn("2025-05-02", appointment.appointment_datetime)
        
        # Date only
        hl7_message2 = r"""MSH|^~\&|SYS|FAC|SYS|FAC|20250502090000||SIU^S12|MSG006|P|2.5
PID|||P002||Test^Patient||1985|M
SCH|002|^^^20250502^^60"""
        
        appointment2 = HL7Parser.parse_siu_message(hl7_message2)
        self.assertIsNotNone(appointment2.appointment_datetime)
        self.assertIn("2025-05-02", appointment2.appointment_datetime)
        
        # Check DOB parsing - note: 1985 should parse to 1985-01-01
        self.assertIsNotNone(appointment2.patient.dob)
        self.assertIn("1985", appointment2.patient.dob)


class TestHL7FileParser(unittest.TestCase):
    
    def test_multiple_messages(self):
        """Test parsing file with multiple messages."""
        file_content = r"""MSH|^~\&|SYS|FAC|SYS|FAC|20250502090000||SIU^S12|MSG001|P|2.5
PID|||P001||Doe^John||19850210|M
SCH|001|^^^20250502100000^^60

MSH|^~\&|SYS|FAC|SYS|FAC|20250502090001||SIU^S12|MSG002|P|2.5
PID|||P002||Smith^Jane||19900315|F
SCH|002|^^^20250502110000^^60"""
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.hl7', delete=False) as f:
            f.write(file_content)
            temp_file = f.name
        
        try:
            appointments = HL7FileParser.parse_file(temp_file)
            self.assertEqual(len(appointments), 2)
            
            self.assertEqual(appointments[0].appointment_id, "001")
            self.assertEqual(appointments[0].patient.first_name, "John")
            self.assertEqual(appointments[0].patient.last_name, "Doe")
            
            self.assertEqual(appointments[1].appointment_id, "002")
            self.assertEqual(appointments[1].patient.first_name, "Jane")
            self.assertEqual(appointments[1].patient.last_name, "Smith")
        
        finally:
            os.unlink(temp_file)
    
    def test_mixed_message_types(self):
        """Test file with mixed SIU and non-SIU messages."""
        file_content = r"""MSH|^~\&|SYS|FAC|SYS|FAC|20250502090000||ADT^A01|MSG001|P|2.5
EVN|A01|20250502090000

MSH|^~\&|SYS|FAC|SYS|FAC|20250502090001||SIU^S12|MSG002|P|2.5
PID|||P001||Doe^John
SCH|001|^^^20250502100000"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.hl7', delete=False) as f:
            f.write(file_content)
            temp_file = f.name
        
        try:
            appointments = HL7FileParser.parse_file(temp_file)
            # Should skip ADT message and only parse SIU
            self.assertEqual(len(appointments), 1)
            self.assertEqual(appointments[0].appointment_id, "001")
        
        finally:
            os.unlink(temp_file)


if __name__ == '__main__':
    unittest.main()