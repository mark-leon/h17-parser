"""
Data models for HL7 SIU appointment parsing.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import json


@dataclass
class Patient:
    """Patient demographic information."""
    id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "dob": self.dob,
            "gender": self.gender
        }


@dataclass
class Provider:
    """Provider information."""
    id: Optional[str] = None
    name: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name
        }


@dataclass
class Appointment:
    """Appointment information."""
    appointment_id: Optional[str] = None
    appointment_datetime: Optional[str] = None
    patient: Optional[Patient] = None
    provider: Optional[Provider] = None
    location: Optional[str] = None
    reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "appointment_id": self.appointment_id,
            "appointment_datetime": self.appointment_datetime,
            "patient": self.patient.to_dict() if self.patient else None,
            "provider": self.provider.to_dict() if self.provider else None,
            "location": self.location,
            "reason": self.reason
        }
    
    def to_json(self, indent: Optional[int] = None) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)


@dataclass
class HL7Message:
    """Raw HL7 message with parsed segments."""
    raw_message: str
    segments: Dict[str, list] = field(default_factory=dict)
    delimiters: Dict[str, str] = field(default_factory=lambda: {
        'field': '|',
        'component': '^',
        'subcomponent': '&',
        'repetition': '~',
        'escape': '\\'
    })
    
    def get_field(self, segment_type: str, field_index: int, component_index: Optional[int] = None) -> Optional[str]:
        """
        Get a field value from a segment.
        
        Args:
            segment_type: Segment type (MSH, PID, etc.)
            field_index: Field index (1-based)
            component_index: Component index (1-based, optional)
        
        Returns:
            Field value or None if not found
        """
        if segment_type not in self.segments:
            return None
        
        segments_of_type = self.segments[segment_type]
        if not segments_of_type:
            return None
        
        # For now, take the first segment of this type
        segment = segments_of_type[0]
        
        if field_index >= len(segment):
            return None
        
        field_value = segment[field_index]
        
        if component_index is not None and field_value:
            components = field_value.split(self.delimiters['component'])
            if component_index < len(components):
                return components[component_index]
        
        return field_value