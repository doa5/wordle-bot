#!/usr/bin/env python3
"""Tests for the Wordle parser module."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from parser import parse_wordle_score, is_wordle_message


def test_parser():
    """Test the Wordle score parser."""
    
    test_cases = [
        # (message, expected_result)
        ("Wordle 1,234 4/6", (1234, 4)),
        ("Wordle 1234 4/6", (1234, 4)),
        ("Wordle 500 X/6", (500, 7)),
        ("Wordle 1 1/6", (1, 1)),
        ("Wordle 9999 6/6", (9999, 6)),
        ("wordle 123 3/6", (123, 3)),  # lowercase
        ("WORDLE 456 2/6", (456, 2)),  # uppercase
        ("Just some text", None),
        ("Almost Wordle but not quite", None),
        ("Wordle but no number", None),
    ]
    
    print("Testing parse_wordle_score()...")
    for message, expected in test_cases:
        result = parse_wordle_score(message)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{message}' -> {result} (expected {expected})")
        assert result == expected, f"Failed for '{message}': got {result}, expected {expected}"
    
    print("\nTesting is_wordle_message()...")
    
    valid_messages = [
        "Wordle 1,234 4/6",
        "Wordle 500 X/6",
        "wordle 123 3/6",
    ]
    
    invalid_messages = [
        "Just some text",
        "Wordle but no number",
        "Random message",
    ]
    
    for message in valid_messages:
        result = is_wordle_message(message)
        status = "✓" if result else "✗"
        print(f"{status} '{message}' -> {result} (expected True)")
        assert result, f"Should be valid: '{message}'"
    
    for message in invalid_messages:
        result = is_wordle_message(message)
        status = "✓" if not result else "✗"
        print(f"{status} '{message}' -> {result} (expected False)")
        assert not result, f"Should be invalid: '{message}'"
    
    print("\n✅ All parser tests passed!")


if __name__ == "__main__":
    test_parser()
