"""Test runner script for all test layers."""
#!/usr/bin/env python3
"""Test runner for APIs project."""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")
    
    try:
        # Use virtual environment if available
        venv_python = "venv/bin/python"
        if os.path.exists(venv_python):
            command = command.replace("python3", venv_python)
        
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(f"Warnings/Errors: {result.stderr}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running {description}:")
        print(f"Return code: {e.returncode}")
        print(f"Error output: {e.stderr}")
        print(f"Standard output: {e.stdout}")
        return False


def run_unit_tests():
    """Run unit tests."""
    return run_command(
        "python3 -m pytest tests/test_unit.py -v --tb=short",
        "Unit Tests"
    )


def run_integration_tests():
    """Run integration tests."""
    return run_command(
        "python3 -m pytest tests/test_integration.py -v --tb=short",
        "Integration Tests"
    )


def run_server_tests():
    """Run server tests."""
    return run_command(
        "python3 -m pytest tests/test_server.py -v --tb=short",
        "Server Tests"
    )


def run_comprehensive_tests():
    """Run comprehensive tests."""
    return run_command(
        "python3 -m pytest tests/test_comprehensive.py -v --tb=short",
        "Comprehensive Tests"
    )


def run_all_tests():
    """Run all tests."""
    return run_command(
        "python3 -m pytest tests/ -v --tb=short",
        "All Tests"
    )


def run_coverage():
    """Run tests with coverage."""
    return run_command(
        "python3 -m pytest tests/ --cov=. --cov-report=html --cov-report=term",
        "Tests with Coverage"
    )


def run_linting():
    """Run code linting."""
    return run_command(
        "python3 -m flake8 . --exclude=venv,__pycache__,.git",
        "Code Linting"
    )


def run_type_checking():
    """Run type checking."""
    return run_command(
        "python3 -m mypy . --ignore-missing-imports",
        "Type Checking"
    )


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description='Test runner for APIs project')
    parser.add_argument('--type', choices=['unit', 'integration', 'server', 'comprehensive', 'all'], 
                       default='all', help='Type of tests to run')
    parser.add_argument('--coverage', action='store_true', help='Run with coverage')
    parser.add_argument('--lint', action='store_true', help='Run linting')
    parser.add_argument('--type-check', action='store_true', help='Run type checking')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Change to project root directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print(f"Running tests from: {os.getcwd()}")
    
    success = True
    
    # Run linting if requested
    if args.lint:
        success &= run_linting()
    
    # Run type checking if requested
    if args.type_check:
        success &= run_type_checking()
    
    # Run tests based on type
    if args.type == 'unit':
        success &= run_unit_tests()
    elif args.type == 'integration':
        success &= run_integration_tests()
    elif args.type == 'server':
        success &= run_server_tests()
    elif args.type == 'comprehensive':
        success &= run_comprehensive_tests()
    elif args.type == 'all':
        if args.coverage:
            success &= run_coverage()
        else:
            success &= run_all_tests()
    
    # Print summary
    print(f"\n{'='*60}")
    if success:
        print("✅ All tests passed successfully!")
    else:
        print("❌ Some tests failed!")
    print(f"{'='*60}")
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
