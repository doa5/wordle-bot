#!/usr/bin/env python3
"""Run all tests for the Wordle bot."""

import subprocess
import sys
import os

def run_tests():
    """Run all tests and report results."""
    tests_dir = os.path.dirname(__file__)
    
    test_files = [
        'test_parser.py',
        'test_database.py'
    ]
    
    print("Running Wordle Bot Tests")
    print("=" * 60)
    
    all_passed = True
    
    for test_file in test_files:
        test_path = os.path.join(tests_dir, test_file)
        print(f"\nRunning {test_file}...")
        print("-" * 60)
        
        result = subprocess.run([sys.executable, test_path], 
                                capture_output=False)
        
        if result.returncode != 0:
            all_passed = False
            print(f"❌ {test_file} FAILED")
        else:
            print(f"✅ {test_file} PASSED")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1

if __name__ == '__main__':
    sys.exit(run_tests())
