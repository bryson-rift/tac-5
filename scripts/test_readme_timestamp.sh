#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get the script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run a test
run_test() {
    local test_name="$1"
    echo -e "${BLUE}Running: $test_name${NC}"
}

# Function to assert test passed
assert_pass() {
    local test_name="$1"
    ((TESTS_PASSED++))
    echo -e "${GREEN}✓ PASSED: $test_name${NC}"
}

# Function to assert test failed
assert_fail() {
    local test_name="$1"
    local reason="$2"
    ((TESTS_FAILED++))
    echo -e "${RED}✗ FAILED: $test_name${NC}"
    echo -e "${RED}  Reason: $reason${NC}"
}

echo -e "${BLUE}=== README Timestamp Script Tests ===${NC}\n"

# Test 1: Default behavior with README.md
run_test "Test 1: Default behavior (README.md)"
TEMP_FILE="$PROJECT_ROOT/test_readme_temp.md"
echo "Test content" > "$TEMP_FILE"
BEFORE_COUNT=$(wc -l < "$TEMP_FILE")
"$SCRIPT_DIR/readme-timestamp.sh" "$TEMP_FILE" > /dev/null 2>&1
AFTER_COUNT=$(wc -l < "$TEMP_FILE")
LAST_LINE=$(tail -n 1 "$TEMP_FILE")

if [[ "$LAST_LINE" =~ ^Last\ updated:\ [0-9]{4}-[0-9]{2}-[0-9]{2}\ [0-9]{2}:[0-9]{2}:[0-9]{2}$ ]]; then
    if [ "$AFTER_COUNT" -gt "$BEFORE_COUNT" ]; then
        assert_pass "Test 1: Default behavior"
    else
        assert_fail "Test 1: Default behavior" "Line count did not increase"
    fi
else
    assert_fail "Test 1: Default behavior" "Timestamp format incorrect: $LAST_LINE"
fi
rm -f "$TEMP_FILE"

# Test 2: Custom file argument
run_test "Test 2: Custom file argument"
CUSTOM_FILE="$PROJECT_ROOT/test_custom_file.txt"
echo "Custom content" > "$CUSTOM_FILE"
"$SCRIPT_DIR/readme-timestamp.sh" "$CUSTOM_FILE" > /dev/null 2>&1
LAST_LINE=$(tail -n 1 "$CUSTOM_FILE")

if [[ "$LAST_LINE" =~ ^Last\ updated:\ [0-9]{4}-[0-9]{2}-[0-9]{2}\ [0-9]{2}:[0-9]{2}:[0-9]{2}$ ]]; then
    assert_pass "Test 2: Custom file argument"
else
    assert_fail "Test 2: Custom file argument" "Timestamp not appended correctly"
fi
rm -f "$CUSTOM_FILE"

# Test 3: File doesn't exist
run_test "Test 3: Non-existent file error handling"
"$SCRIPT_DIR/readme-timestamp.sh" "/tmp/nonexistent_file_xyz123.md" > /dev/null 2>&1
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    assert_pass "Test 3: Non-existent file error handling"
else
    assert_fail "Test 3: Non-existent file error handling" "Script should have exited with error"
fi

# Test 4: Read-only file
run_test "Test 4: Read-only file error handling"
READONLY_FILE="$PROJECT_ROOT/test_readonly.txt"
echo "Read-only content" > "$READONLY_FILE"
chmod 444 "$READONLY_FILE"
"$SCRIPT_DIR/readme-timestamp.sh" "$READONLY_FILE" > /dev/null 2>&1
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    assert_pass "Test 4: Read-only file error handling"
else
    assert_fail "Test 4: Read-only file error handling" "Script should have detected write permission error"
fi
chmod 644 "$READONLY_FILE"
rm -f "$READONLY_FILE"

# Test 5: Timestamp format validation
run_test "Test 5: Timestamp format validation"
FORMAT_FILE="$PROJECT_ROOT/test_format.txt"
echo "Format test" > "$FORMAT_FILE"
"$SCRIPT_DIR/readme-timestamp.sh" "$FORMAT_FILE" > /dev/null 2>&1
TIMESTAMP=$(tail -n 1 "$FORMAT_FILE" | sed 's/Last updated: //')

if [[ "$TIMESTAMP" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}\ [0-9]{2}:[0-9]{2}:[0-9]{2}$ ]]; then
    assert_pass "Test 5: Timestamp format validation"
else
    assert_fail "Test 5: Timestamp format validation" "Format does not match YYYY-MM-DD HH:MM:SS"
fi
rm -f "$FORMAT_FILE"

# Test 6: Pacific Time zone verification
run_test "Test 6: Pacific Time zone verification"
PT_FILE="$PROJECT_ROOT/test_pacific.txt"
echo "Pacific time test" > "$PT_FILE"
BEFORE_TIME=$(TZ='America/Los_Angeles' date '+%Y-%m-%d %H:%M')
"$SCRIPT_DIR/readme-timestamp.sh" "$PT_FILE" > /dev/null 2>&1
TIMESTAMP=$(tail -n 1 "$PT_FILE" | sed 's/Last updated: //' | cut -d' ' -f1,2 | cut -d':' -f1,2)
AFTER_TIME=$(TZ='America/Los_Angeles' date '+%Y-%m-%d %H:%M')

# Check if timestamp is within reasonable range (between before and after)
if [[ "$TIMESTAMP" == "$BEFORE_TIME" || "$TIMESTAMP" == "$AFTER_TIME" ]]; then
    assert_pass "Test 6: Pacific Time zone verification"
else
    assert_fail "Test 6: Pacific Time zone verification" "Timestamp $TIMESTAMP not in Pacific Time range"
fi
rm -f "$PT_FILE"

# Test 7: Multiple runs append multiple timestamps
run_test "Test 7: Multiple runs append correctly"
MULTI_FILE="$PROJECT_ROOT/test_multi.txt"
echo "Multi-run test" > "$MULTI_FILE"
"$SCRIPT_DIR/readme-timestamp.sh" "$MULTI_FILE" > /dev/null 2>&1
sleep 1
"$SCRIPT_DIR/readme-timestamp.sh" "$MULTI_FILE" > /dev/null 2>&1
COUNT=$(grep -c "Last updated:" "$MULTI_FILE")

if [ "$COUNT" -eq 2 ]; then
    assert_pass "Test 7: Multiple runs append correctly"
else
    assert_fail "Test 7: Multiple runs append correctly" "Expected 2 timestamps, found $COUNT"
fi
rm -f "$MULTI_FILE"

# Test 8: Empty file handling
run_test "Test 8: Empty file handling"
EMPTY_FILE="$PROJECT_ROOT/test_empty.txt"
touch "$EMPTY_FILE"
"$SCRIPT_DIR/readme-timestamp.sh" "$EMPTY_FILE" > /dev/null 2>&1
EXIT_CODE=$?
LAST_LINE=$(tail -n 1 "$EMPTY_FILE")

if [ $EXIT_CODE -eq 0 ] && [[ "$LAST_LINE" =~ ^Last\ updated: ]]; then
    assert_pass "Test 8: Empty file handling"
else
    assert_fail "Test 8: Empty file handling" "Failed to append to empty file"
fi
rm -f "$EMPTY_FILE"

# Summary
echo -e "\n${BLUE}=== Test Summary ===${NC}"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed!${NC}"
    exit 1
fi
