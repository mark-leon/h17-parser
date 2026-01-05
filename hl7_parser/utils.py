"""
Utility functions for HL7 parsing.
"""
from typing import Optional
from datetime import datetime
import re


def parse_hl7_timestamp(hl7_timestamp: str) -> Optional[str]:
    """
    Convert HL7 timestamp to ISO 8601 format.
    
    HL7 timestamps can be in various formats:
    - YYYYMMDDHHMMSS[+/-ZZZZ]
    - YYYYMMDDHHMM
    - YYYYMMDD
    - YYYY
    
    Args:
        hl7_timestamp: HL7 timestamp string
    
    Returns:
        ISO 8601 formatted string or None if invalid
    """
    if not hl7_timestamp or not hl7_timestamp.strip():
        return None
    
    timestamp = hl7_timestamp.strip()
    
    # Remove timezone offset for parsing
    timezone_offset = None
    if '+' in timestamp:
        timestamp, timezone_offset = timestamp.split('+')
    elif '-' in timestamp and timestamp.count('-') > 2:  # Only split if not part of date
        # Check if it's a timezone offset (at least 4 chars after -)
        match = re.search(r'([+-]\d{4})$', timestamp)
        if match:
            timezone_offset = match.group(0)
            timestamp = timestamp[:-5]
    
    # Determine format based on length
    timestamp_len = len(timestamp)
    
    try:
        if timestamp_len >= 14:  # YYYYMMDDHHMMSS
            dt = datetime.strptime(timestamp[:14], '%Y%m%d%H%M%S')
        elif timestamp_len >= 12:  # YYYYMMDDHHMM
            dt = datetime.strptime(timestamp[:12], '%Y%m%d%H%M')
        elif timestamp_len >= 8:  # YYYYMMDD
            dt = datetime.strptime(timestamp[:8], '%Y%m%d')
        elif timestamp_len >= 4:  # YYYY
            dt = datetime.strptime(timestamp[:4], '%Y')
        else:
            return None
        
        # Format as ISO 8601
        iso_format = dt.isoformat()
        
        # Add timezone if provided
        if timezone_offset:
            if timezone_offset.startswith('+') or timezone_offset.startswith('-'):
                if len(timezone_offset) == 5:  # ±HHMM
                    hours = int(timezone_offset[1:3])
                    minutes = int(timezone_offset[3:5])
                    if timezone_offset.startswith('-'):
                        hours = -hours
                        minutes = -minutes
                    # Convert to UTC offset format
                    iso_format += f"{timezone_offset[:3]}:{timezone_offset[3:]}"
        
        return iso_format
    except ValueError:
        return None


def parse_name(hl7_name: str) -> tuple:
    """
    Parse HL7 name field into components.
    
    HL7 name format: Last^First^Middle^Suffix^Prefix
    
    Args:
        hl7_name: HL7 formatted name string
    
    Returns:
        Tuple of (last_name, first_name, full_name)
    """
    if not hl7_name:
        return None, None, None
    
    components = hl7_name.split('^')
    
    last_name = components[0] if len(components) > 0 and components[0] else None
    first_name = components[1] if len(components) > 1 and components[1] else None
    middle_name = components[2] if len(components) > 2 and components[2] else None
    suffix = components[3] if len(components) > 3 and components[3] else None
    prefix = components[4] if len(components) > 4 and components[4] else None
    
    # Construct full name
    name_parts = []
    if prefix:
        name_parts.append(prefix)
    if first_name:
        name_parts.append(first_name)
    if middle_name:
        name_parts.append(middle_name)
    if last_name:
        name_parts.append(last_name)
    if suffix:
        name_parts.append(suffix)
    
    full_name = ' '.join(name_parts) if name_parts else None
    
    return last_name, first_name, full_name


def safe_split(text: str, delimiter: str, maxsplit: int = -1) -> list:
    """
    Safely split text by delimiter, handling None and empty strings.
    
    Args:
        text: Text to split
        delimiter: Delimiter character
        maxsplit: Maximum number of splits
    
    Returns:
        List of split parts
    """
    if not text:
        return []
    return text.split(delimiter, maxsplit)