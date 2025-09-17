# run_tests.py
#!/usr/bin/env python3
import os
import sys
import pytest

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == '__main__':
    # Run tests with verbose output
    exit_code = pytest.main(['-v', 'tests/'])
    sys.exit(exit_code)