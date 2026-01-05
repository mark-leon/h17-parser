# HL7 SIU Appointment Parser

A robust Python parser for HL7 SIU S12 appointment messages that converts HL7 v2.x format to structured JSON.

## Features

- Parses HL7 SIU S12 appointment messages
- Converts to normalized JSON structure
- Handles real-world HL7 inconsistencies
- Robust error handling and validation
- Support for multiple messages per file
- Command-line interface
- Docker support

## Installation

### From source

```bash
git clone <repository-url>
cd hl7_parser
pip install -e .
```

Usage
Command Line
bash

# Parse a single file

python -m hl7_parser.cli input.hl7

# Parse and pretty print

python -m hl7_parser.cli input.hl7 --pretty

# Parse and save to file

python -m hl7_parser.cli input.hl7 --output appointments.json

# Using installed package

hl7-parser input.hl7 --pretty
