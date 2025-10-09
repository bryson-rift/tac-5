#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get the script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"

# Default to README.md if no argument provided
TARGET_FILE="${1:-$PROJECT_ROOT/README.md}"

# Convert to absolute path if relative
if [[ "$TARGET_FILE" != /* ]]; then
    TARGET_FILE="$PROJECT_ROOT/$TARGET_FILE"
fi

echo -e "${BLUE}Appending timestamp to file...${NC}"

# Check if file exists
if [ ! -f "$TARGET_FILE" ]; then
    echo -e "${RED}✗ Error: File does not exist: $TARGET_FILE${NC}"
    exit 1
fi

# Check if file is writable
if [ ! -w "$TARGET_FILE" ]; then
    echo -e "${RED}✗ Error: File is not writable: $TARGET_FILE${NC}"
    exit 1
fi

# Generate Pacific Time timestamp
TIMESTAMP=$(TZ='America/Los_Angeles' date '+%Y-%m-%d %H:%M:%S')

# Check if file ends with a newline, if not add one
if [ -s "$TARGET_FILE" ]; then
    LAST_CHAR=$(tail -c 1 "$TARGET_FILE")
    if [ -n "$LAST_CHAR" ]; then
        echo "" >> "$TARGET_FILE"
    fi
fi

# Append timestamp to file
echo "Last updated: $TIMESTAMP" >> "$TARGET_FILE"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Timestamp appended successfully to $TARGET_FILE${NC}"
    echo -e "${BLUE}Timestamp: $TIMESTAMP${NC}"
    exit 0
else
    echo -e "${RED}✗ Error: Failed to append timestamp${NC}"
    exit 1
fi
