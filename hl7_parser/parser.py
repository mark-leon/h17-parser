"""
Main HL7 SIU message parser.
"""
import re
from typing import List, Optional, Dict, Any
from .models import HL7Message, Appointment, Patient, Provider
from .exceptions import InvalidMessageError, HL7ParseError
from .utils import parse_hl7_timestamp, parse_name, safe_split


class HL7Parser:
    """Parser for HL7 SIU S12 messages."""
    
    @staticmethod
    def parse_message(raw_message: str) -> HL7Message:
        """
        Parse raw HL7 message into structured format.
        
        Args:
            raw_message: Raw HL7 message string
        
        Returns:
            HL7Message object with parsed segments
        
        Raises:
            InvalidMessageError: If message is invalid
        """
        if not raw_message or not raw_message.strip():
            raise InvalidMessageError("Empty message")
        
        # Normalize line endings
        message = raw_message.replace('\r\n', '\r').replace('\n', '\r')
        
        # Split into segments
        segments = message.strip().split('\r')
        if not segments:
            raise InvalidMessageError("No segments found")
        
        # Parse MSH segment to get delimiters
        if not segments[0].startswith('MSH'):
            raise InvalidMessageError("Message must start with MSH segment")
        
        # Parse delimiters from MSH segment
        msh_segment = segments[0]
        if len(msh_segment) < 4:
            raise InvalidMessageError("Invalid MSH segment")
        
        field_delimiter = msh_segment[3]  # MSH.1 is the field delimiter
        delimiters = {
            'field': field_delimiter,
            'component': '^',  # Default, can be overridden by MSH.2
            'subcomponent': '&',
            'repetition': '~',
            'escape': '\\'
        }
        
        # Parse MSH.2 for encoding characters if present
        if len(msh_segment) > 4 and msh_segment[4] == field_delimiter:
            # MSH.2 contains component, repetition, escape, and subcomponent delimiters
            encoding_chars = msh_segment[5:9]
            if len(encoding_chars) >= 4:
                delimiters['component'] = encoding_chars[0]
                delimiters['repetition'] = encoding_chars[1]
                delimiters['escape'] = encoding_chars[2]
                delimiters['subcomponent'] = encoding_chars[3]
        
        # Parse all segments
        parsed_segments: Dict[str, List[List[str]]] = {}
        
        for segment in segments:
            if not segment:
                continue
            
            # Extract segment type (first 3 characters)
            segment_type = segment[:3]
            
            # Split segment into fields
            fields = segment.split(delimiters['field'])
            
            # Store segment
            if segment_type not in parsed_segments:
                parsed_segments[segment_type] = []
            parsed_segments[segment_type].append(fields)
        
        return HL7Message(
            raw_message=raw_message,
            segments=parsed_segments,
            delimiters=delimiters
        )
    
    @staticmethod
    def validate_siu_message(message: HL7Message) -> bool:
        """
        Validate that the message is an SIU S12 message.
        
        Args:
            message: Parsed HL7 message
        
        Returns:
            True if valid SIU S12 message
        
        Raises:
            InvalidMessageError: If not a valid SIU S12 message
        """
        # Check MSH segment exists
        if 'MSH' not in message.segments:
            raise InvalidMessageError("MSH segment missing")
        
        # Get MSH fields
        msh_fields = message.segments['MSH'][0]
        
        # Check message type (MSH.9)
        if len(msh_fields) <= 8:
            raise InvalidMessageError("MSH segment missing message type field")
        
        message_type = msh_fields[8]
        if '^' in message_type:
            msg_type, trigger_event = message_type.split('^')[:2]
        else:
            msg_type = message_type
        
        if msg_type != 'SIU':
            raise InvalidMessageError(f"Expected SIU message type, got {msg_type}")
        
        # Check trigger event (optional)
        if '^' in message_type and trigger_event != 'S12':
            # We'll parse it anyway but log/warn about unexpected trigger
            pass
        
        return True
    
    @staticmethod
    def extract_appointment(message: HL7Message) -> Appointment:
        """
        Extract appointment information from parsed HL7 message.
        
        Args:
            message: Parsed HL7 message
        
        Returns:
            Appointment object with extracted data
        """
        appointment = Appointment()
        
        # Extract from SCH segment
        if 'SCH' in message.segments:
            sch_fields = message.segments['SCH'][0]
            
            # Appointment ID (SCH.1)
            if len(sch_fields) > 1 and sch_fields[1]:
                appointment.appointment_id = sch_fields[1]
            
            # Appointment datetime (SCH.11.4)
            if len(sch_fields) > 11 and sch_fields[11]:
                # SCH.11 is a composite field: ^^^datetime^^duration
                components = safe_split(sch_fields[11], message.delimiters['component'])
                if len(components) > 3 and components[3]:
                    appointment.appointment_datetime = parse_hl7_timestamp(components[3])
            
            # Reason (SCH.4)
            if len(sch_fields) > 4 and sch_fields[4]:
                appointment.reason = sch_fields[4]
            
            # Location (SCH.6.3)
            if len(sch_fields) > 6 and sch_fields[6]:
                components = safe_split(sch_fields[6], message.delimiters['component'])
                if len(components) > 2 and components[2]:
                    appointment.location = components[2]
            
            # Provider from SCH.10
            if len(sch_fields) > 10 and sch_fields[10]:
                components = safe_split(sch_fields[10], message.delimiters['component'])
                provider_id = components[0] if len(components) > 0 and components[0] else None
                provider_name_field = components[1] if len(components) > 1 and components[1] else None
                
                if provider_id or provider_name_field:
                    provider = Provider()
                    provider.id = provider_id
                    
                    if provider_name_field:
                        last_name, first_name, full_name = parse_name(provider_name_field)
                        provider.name = full_name or f"{first_name or ''} {last_name or ''}".strip()
                    
                    appointment.provider = provider
        
        # Extract patient information from PID segment
        if 'PID' in message.segments:
            pid_fields = message.segments['PID'][0]
            patient = Patient()
            
            # Patient ID (PID.3)
            if len(pid_fields) > 3 and pid_fields[3]:
                patient.id = pid_fields[3]
            
            # Patient name (PID.5)
            if len(pid_fields) > 5 and pid_fields[5]:
                last_name, first_name, _ = parse_name(pid_fields[5])
                patient.last_name = last_name
                patient.first_name = first_name
            
            # Date of birth (PID.7)
            if len(pid_fields) > 7 and pid_fields[7]:
                patient.dob = parse_hl7_timestamp(pid_fields[7])
            
            # Gender (PID.8)
            if len(pid_fields) > 8 and pid_fields[8]:
                patient.gender = pid_fields[8]
            
            appointment.patient = patient
        
        # Extract provider from PV1 segment (overrides SCH if present)
        if 'PV1' in message.segments:
            pv1_fields = message.segments['PV1'][0]
            
            # Provider (PV1.7)
            if len(pv1_fields) > 7 and pv1_fields[7]:
                components = safe_split(pv1_fields[7], message.delimiters['component'])
                provider_id = components[0] if len(components) > 0 and components[0] else None
                provider_name_field = components[1] if len(components) > 1 and components[1] else None
                
                if provider_id or provider_name_field:
                    provider = appointment.provider or Provider()
                    provider.id = provider_id or provider.id
                    
                    if provider_name_field:
                        last_name, first_name, full_name = parse_name(provider_name_field)
                        provider.name = full_name or f"{first_name or ''} {last_name or ''}".strip()
                    
                    appointment.provider = provider
            
            # Location from PV1.3 (overrides SCH if present)
            if len(pv1_fields) > 3 and pv1_fields[3]:
                components = safe_split(pv1_fields[3], message.delimiters['component'])
                if len(components) > 1 and components[1]:
                    appointment.location = components[1]
        
        return appointment
    
    @staticmethod
    def parse_siu_message(raw_message: str) -> Appointment:
        """
        Parse a single SIU S12 message.
        
        Args:
            raw_message: Raw HL7 message string
        
        Returns:
            Appointment object
        
        Raises:
            InvalidMessageError: If not a valid SIU S12 message
            HL7ParseError: For other parsing errors
        """
        try:
            # Parse raw message
            message = HL7Parser.parse_message(raw_message)
            
            # Validate it's an SIU message
            HL7Parser.validate_siu_message(message)
            
            # Extract appointment data
            appointment = HL7Parser.extract_appointment(message)
            
            return appointment
        
        except Exception as e:
            if isinstance(e, HL7ParseError):
                raise
            raise HL7ParseError(f"Error parsing HL7 message: {str(e)}") from e


class HL7FileParser:
    """Parser for HL7 files containing one or more messages."""
    
    @staticmethod
    def split_messages(file_content: str) -> List[str]:
        """
        Split file content into individual HL7 messages.
        
        Args:
            file_content: Complete file content
        
        Returns:
            List of individual HL7 messages
        """
        # Normalize line endings
        content = file_content.replace('\r\n', '\r').replace('\n', '\r')
        
        # Split by MSH segments (each message starts with MSH)
        messages = []
        current_message = []
        
        for line in content.split('\r'):
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('MSH'):
                if current_message:
                    messages.append('\r'.join(current_message))
                    current_message = []
            
            current_message.append(line)
        
        if current_message:
            messages.append('\r'.join(current_message))
        
        return messages
    
    @staticmethod
    def parse_file(filepath: str) -> List[Appointment]:
        """
        Parse an HL7 file containing one or more SIU messages.
        
        Args:
            filepath: Path to HL7 file
        
        Returns:
            List of Appointment objects
        
        Raises:
            FileNotFoundError: If file doesn't exist
            HL7ParseError: For parsing errors
        """
        try:
            with open(filepath, 'r') as f:
                content = f.read()
        except IOError as e:
            raise FileNotFoundError(f"Could not read file {filepath}: {str(e)}")
        
        # Split into individual messages
        raw_messages = HL7FileParser.split_messages(content)
        
        appointments = []
        
        for i, raw_message in enumerate(raw_messages):
            try:
                appointment = HL7Parser.parse_siu_message(raw_message)
                appointments.append(appointment)
            except InvalidMessageError:
                # Skip non-SIU messages
                continue
            except HL7ParseError as e:
                # Log error but continue processing other messages
                print(f"Warning: Error parsing message {i+1}: {str(e)}")
                continue
        
        return appointments