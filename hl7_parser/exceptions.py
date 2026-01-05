"""
Custom exceptions for HL7 parsing errors.
"""

class HL7ParseError(Exception):
    """Base exception for HL7 parsing errors."""
    pass


class InvalidMessageError(HL7ParseError):
    """Raised when the message is invalid or of wrong type."""
    pass


class MissingSegmentError(HL7ParseError):
    """Raised when a required segment is missing."""
    pass


class InvalidTimestampError(HL7ParseError):
    """Raised when a timestamp cannot be parsed."""
    pass


class FieldParseError(HL7ParseError):
    """Raised when a field cannot be parsed."""
    pass