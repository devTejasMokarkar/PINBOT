#!/usr/bin/env python3
"""
Test Runner Script

Comprehensive test execution with coverage reporting and performance analysis.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*60)
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False

def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description="Run AI Service Test Suite")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--performance", action="store_true", help="Run performance tests only")
    parser.add_argument("--redis", action="store_true", help="Run Redis-dependent tests")
    parser.add_argument("--coverage", action="store_true", default=True, help="Generate coverage report")
    parser.add_argument("--html", action="store_true", help="Generate HTML coverage report")
    parser.add_argument("--fail-under", type=int, default=80, help="Coverage threshold")
    parser.add_argument("--parallel", type=int, help="Number of parallel processes")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--benchmark", action="store_true", help="Run benchmark tests")
    
    args = parser.parse_args()
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # Base pytest command
    pytest_cmd = ["python", "-m", "pytest"]
    
    # Add coverage options
    if args.coverage:
        pytest_cmd.extend([
            "--cov=src",
            "--cov=tests",
            f"--cov-fail-under={args.fail_under}"
        ])
        
        if args.html:
            pytest_cmd.extend(["--cov-report=html:htmlcov"])
        
        pytest_cmd.extend(["--cov-report=term-missing"])
        pytest_cmd.extend(["--cov-report=xml:coverage.xml"])
    
    # Add verbose option
    if args.verbose:
        pytest_cmd.append("-v")
    
    # Add parallel execution
    if args.parallel:
        pytest_cmd.extend(["-n", str(args.parallel)])
    
    # Add benchmark option
    if args.benchmark:
        pytest_cmd.extend(["--benchmark-only"])
    
    # Determine which tests to run
    test_markers = []
    
    if args.unit:
        test_markers.append("unit")
    elif args.integration:
        test_markers.append("integration")
    elif args.performance:
        test_markers.append("performance")
    elif args.redis:
        test_markers.append("redis")
    else:
        # Run all tests by default
        test_markers = ["unit", "integration"]
        if not args.redis:
            # Skip Redis tests unless explicitly requested
            pytest_cmd.extend(["-m", "not redis"])
    
    # Add markers to command
    if test_markers:
        marker_expr = " or ".join(test_markers)
        pytest_cmd.extend(["-m", marker_expr])
    
    # Add test directory
    pytest_cmd.append("tests/")
    
    print(f"\n{'='*80}")
    print("AI Service Test Suite")
    print(f"{'='*80}")
    print(f"Project Directory: {project_dir}")
    print(f"Python Version: {sys.version}")
    print(f"Test Command: {' '.join(pytest_cmd)}")
    print(f"{'='*80}")
    
    # Run tests
    success = run_command(pytest_cmd, "Test Suite")
    
    if success:
        print(f"\n{'='*60}")
        print("TESTS PASSED! ")
        print(f"{'='*60}")
        
        if args.coverage:
            print(f"\nCoverage Report Generated:")
            print(f"- Terminal: Displayed above")
            if args.html:
                print(f"- HTML: {project_dir}/htmlcov/index.html")
            print(f"- XML: {project_dir}/coverage.xml")
            print(f"- Threshold: {args.fail_under}%")
        
        if args.benchmark:
            print(f"\nBenchmark Report Generated:")
            print(f"- Check pytest output for performance metrics")
    
    else:
        print(f"\n{'='*60}")
        print("TESTS FAILED! ")
        print(f"{'='*60}")
        sys.exit(1)

if __name__ == "__main__":
    main()
