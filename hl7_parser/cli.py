"""
Command line interface for HL7 parser.
"""
import argparse
import json
import sys
from typing import List
from .parser import HL7FileParser
from .models import Appointment


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Parse HL7 SIU S12 messages from file'
    )
    parser.add_argument(
        'input_file',
        help='Path to HL7 file'
    )
    parser.add_argument(
        '--output',
        '-o',
        help='Output file (default: stdout)'
    )
    parser.add_argument(
        '--pretty',
        '-p',
        action='store_true',
        help='Pretty print JSON output'
    )
    parser.add_argument(
        '--errors',
        '-e',
        choices=['skip', 'fail', 'warn'],
        default='warn',
        help='How to handle parsing errors (skip, fail, warn)'
    )
    
    args = parser.parse_args()
    
    try:
        # Parse file
        appointments = HL7FileParser.parse_file(args.input_file)
        
        # Convert to JSON
        indent = 2 if args.pretty else None
        appointments_dict = [app.to_dict() for app in appointments]
        output_json = json.dumps(
            appointments_dict,
            indent=indent,
            default=str
        )
        
        # Output
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output_json)
            print(f"Parsed {len(appointments)} appointments to {args.output}")
        else:
            print(output_json)
        
        return 0
    
    except FileNotFoundError as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())