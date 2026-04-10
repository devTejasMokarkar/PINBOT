#!/bin/bash

# =============================================================================
# AI Service Test Runner Script
# =============================================================================
# Comprehensive test execution script for AI Service with coverage reporting
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Print colored output
print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================${NC}"
}

print_success() {
    echo -e "${GREEN}SUCCESS: $1${NC}"
}

print_error() {
    echo -e "${RED}ERROR: $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}WARNING: $1${NC}"
}

print_info() {
    echo -e "${CYAN}INFO: $1${NC}"
}

# Check if virtual environment is activated
check_venv() {
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        print_warning "Virtual environment not activated"
        print_info "Activating virtual environment..."
        
        if [[ -f "venv/bin/activate" ]]; then
            source venv/bin/activate
            print_success "Virtual environment activated"
        else
            print_error "Virtual environment not found at venv/bin/activate"
            print_info "Please create virtual environment first:"
            echo "  python -m venv venv"
            echo "  source venv/bin/activate"
            echo "  pip install -r requirements.txt"
            exit 1
        fi
    else
        print_success "Virtual environment is active: $VIRTUAL_ENV"
    fi
}

# Install test dependencies if needed
install_test_deps() {
    print_header "Installing Test Dependencies"
    
    if ! pip list | grep -q "pytest"; then
        print_info "Installing pytest and test dependencies..."
        pip install pytest pytest-asyncio pytest-cov pytest-mock pytest-xdist
        print_success "Test dependencies installed"
    else
        print_success "Test dependencies already installed"
    fi
}

# Run unit tests
run_unit_tests() {
    print_header "Running Unit Tests"
    
    print_info "Executing unit tests with coverage..."
    
    python -m pytest tests/test_unit/ \
        -v \
        --cov=src \
        --cov-report=term-missing \
        --cov-report=html:htmlcov/unit \
        --cov-report=xml:coverage-unit.xml \
        --cov-fail-under=80 \
        --tb=short \
        -m "unit" || {
        print_error "Unit tests failed"
        return 1
    }
    
    print_success "Unit tests completed successfully"
    print_info "Coverage report: htmlcov/unit/index.html"
}

# Run integration tests
run_integration_tests() {
    print_header "Running Integration Tests"
    
    print_info "Executing integration tests..."
    
    python -m pytest tests/test_integration/ \
        -v \
        --cov=src \
        --cov-append \
        --cov-report=term-missing \
        --cov-report=html:htmlcov/integration \
        --cov-report=xml:coverage-integration.xml \
        --tb=short \
        -m "integration" || {
        print_error "Integration tests failed"
        return 1
    }
    
    print_success "Integration tests completed successfully"
    print_info "Coverage report: htmlcov/integration/index.html"
}

# Run performance tests
run_performance_tests() {
    print_header "Running Performance Tests"
    
    print_info "Executing performance tests..."
    
    python -m pytest tests/test_performance/ \
        -v \
        --tb=short \
        -m "performance" --slow || {
        print_warning "Performance tests failed (non-critical)"
        return 0
    }
    
    print_success "Performance tests completed successfully"
}

# Run Redis tests (if Redis is available)
run_redis_tests() {
    print_header "Running Redis Tests"
    
    # Check if Redis is running
    if ! command -v redis-cli &> /dev/null; then
        print_warning "Redis CLI not found, skipping Redis tests"
        return 0
    fi
    
    if ! redis-cli ping &> /dev/null; then
        print_warning "Redis server not running, skipping Redis tests"
        print_info "To run Redis tests:"
        echo "  1. Install Redis: sudo apt-get install redis-server"
        echo "  2. Start Redis: sudo systemctl start redis"
        echo "  3. Run Redis tests: ./test_runner.sh --redis"
        return 0
    fi
    
    print_info "Executing Redis-dependent tests..."
    
    python -m pytest tests/ \
        -v \
        --tb=short \
        -m "redis" || {
        print_warning "Redis tests failed (non-critical)"
        return 0
    }
    
    print_success "Redis tests completed successfully"
}

# Run all tests
run_all_tests() {
    print_header "Running Complete Test Suite"
    
    print_info "Starting comprehensive test execution..."
    
    # Create coverage directory
    mkdir -p htmlcov
    
    # Run test suites
    run_unit_tests || return 1
    run_integration_tests || return 1
    run_performance_tests
    run_redis_tests
    
    # Generate combined coverage report
    print_header "Generating Combined Coverage Report"
    
    python -m pytest tests/ \
        --cov=src \
        --cov-append \
        --cov-report=html:htmlcov/combined \
        --cov-report=xml:coverage-combined.xml \
        --cov-report=term-missing \
        --cov-fail-under=80 \
        --tb=short \
        -m "unit or integration" || {
        print_error "Combined coverage below threshold"
        return 1
    }
    
    print_success "All tests completed successfully"
    print_info "Combined coverage report: htmlcov/combined/index.html"
}

# Run quick tests (unit only)
run_quick_tests() {
    print_header "Running Quick Tests (Unit Only)"
    
    python -m pytest tests/test_unit/ \
        -v \
        --tb=short \
        -m "unit" || {
        print_error "Quick tests failed"
        return 1
    }
    
    print_success "Quick tests completed successfully"
}

# Run tests with parallel execution
run_parallel_tests() {
    local workers=${1:-4}
    print_header "Running Parallel Tests ($workers workers)"
    
    python -m pytest tests/ \
        -v \
        -n "$workers" \
        --cov=src \
        --cov-report=term-missing \
        --cov-report=html:htmlcov/parallel \
        --cov-fail-under=80 \
        --tb=short \
        -m "unit or integration" || {
        print_error "Parallel tests failed"
        return 1
    }
    
    print_success "Parallel tests completed successfully"
    print_info "Coverage report: htmlcov/parallel/index.html"
}

# Run benchmark tests
run_benchmark_tests() {
    print_header "Running Benchmark Tests"
    
    if ! pip list | grep -q "pytest-benchmark"; then
        print_info "Installing pytest-benchmark..."
        pip install pytest-benchmark
    fi
    
    python -m pytest tests/test_performance/ \
        --benchmark-only \
        --benchmark-sort=mean \
        --benchmark-json=benchmark_results.json \
        -v \
        -m "performance" || {
        print_warning "Benchmark tests failed"
        return 0
    }
    
    print_success "Benchmark tests completed successfully"
    print_info "Benchmark results: benchmark_results.json"
}

# Generate test report
generate_report() {
    print_header "Generating Test Report"
    
    local report_file="test_report_$(date +%Y%m%d_%H%M%S).txt"
    
    cat > "$report_file" << EOF
AI Service Test Report
=====================

Date: $(date)
Python: $(python --version)
Project: $PROJECT_ROOT

Test Results:
-------------
Unit Tests: $(python -m pytest tests/test_unit/ -q --tb=no | grep -E "passed|failed" || echo "Not run")
Integration Tests: $(python -m pytest tests/test_integration/ -q --tb=no | grep -E "passed|failed" || echo "Not run")
Performance Tests: $(python -m pytest tests/test_performance/ -q --tb=no | grep -E "passed|failed" || echo "Not run")

Coverage Reports:
-----------------
Unit Coverage: htmlcov/unit/index.html
Integration Coverage: htmlcov/integration/index.html
Combined Coverage: htmlcov/combined/index.html
XML Reports: coverage-*.xml

Performance:
-----------
Benchmark Results: benchmark_results.json (if available)

System Info:
-----------
OS: $(uname -s)
Memory: $(free -h | grep Mem)
Disk: $(df -h . | tail -1)

EOF
    
    print_success "Test report generated: $report_file"
}

# Clean up test artifacts
cleanup() {
    print_header "Cleaning Up Test Artifacts"
    
    # Remove coverage files
    rm -f .coverage
    rm -f coverage*.xml
    rm -f benchmark_results.json
    rm -f .pytest_cache
    
    # Remove HTML coverage directories
    rm -rf htmlcov
    
    # Remove test reports
    rm -f test_report_*.txt
    
    print_success "Test artifacts cleaned up"
}

# Show help
show_help() {
    cat << EOF
AI Service Test Runner
=====================

Usage: $0 [COMMAND] [OPTIONS]

COMMANDS:
    all                 Run all tests (unit + integration + performance)
    unit                Run unit tests only
    integration         Run integration tests only
    performance         Run performance tests only
    redis               Run Redis-dependent tests
    quick               Run quick tests (unit only, no coverage)
    parallel [N]        Run tests in parallel (default: 4 workers)
    benchmark           Run benchmark tests
    report              Generate test report
    cleanup             Clean up test artifacts
    help                Show this help message

EXAMPLES:
    $0                          # Run all tests
    $0 unit                     # Run unit tests only
    $0 integration              # Run integration tests only
    $0 parallel 8               # Run tests with 8 workers
    $0 redis                    # Run Redis tests
    $0 benchmark                # Run performance benchmarks
    $0 cleanup                  # Clean up artifacts

COVERAGE REPORTS:
    Unit tests:         htmlcov/unit/index.html
    Integration tests:  htmlcov/integration/index.html
    Combined coverage:  htmlcov/combined/index.html

REQUIREMENTS:
    - Python 3.8+
    - Virtual environment activated
    - Test dependencies installed
    - Redis server (for Redis tests)

EOF
}

# Main execution logic
main() {
    local command=${1:-"all"}
    
    print_header "AI Service Test Runner"
    print_info "Project: $PROJECT_ROOT"
    print_info "Command: $command"
    
    # Check virtual environment
    check_venv
    
    # Install test dependencies
    install_test_deps
    
    # Execute command
    case "$command" in
        "all")
            run_all_tests
            generate_report
            ;;
        "unit")
            run_unit_tests
            ;;
        "integration")
            run_integration_tests
            ;;
        "performance")
            run_performance_tests
            ;;
        "redis")
            run_redis_tests
            ;;
        "quick")
            run_quick_tests
            ;;
        "parallel")
            run_parallel_tests "$2"
            ;;
        "benchmark")
            run_benchmark_tests
            ;;
        "report")
            generate_report
            ;;
        "cleanup")
            cleanup
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
    
    print_header "Test Runner Completed"
    print_success "Command '$command' executed successfully"
}

# Trap to handle script interruption
trap 'print_warning "Test runner interrupted"; exit 1' INT TERM

# Run main function with all arguments
main "$@"
