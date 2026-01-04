#!/usr/bin/env python
"""
Test runner for Notev unit tests.
Run all tests or specific test modules.
"""
import sys
import unittest


def run_all_tests():
    """Run all unit tests."""
    loader = unittest.TestLoader()
    suite = loader.discover('tests', pattern='test_*.py')

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return 0 if result.wasSuccessful() else 1


def run_specific_test(test_name):
    """Run a specific test module."""
    loader = unittest.TestLoader()

    # Try to load the specific test
    try:
        suite = loader.loadTestsFromName(f'tests.{test_name}')
    except Exception as e:
        print(f"Error loading test '{test_name}': {e}")
        return 1

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Run specific test
        exit_code = run_specific_test(sys.argv[1])
    else:
        # Run all tests
        print("Running all tests...\n")
        exit_code = run_all_tests()

    sys.exit(exit_code)
