#!/bin/bash

# ADW Webhook Starter Script
# Safely starts the webhook server with automatic cleanup and optional ngrok tunnel

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
ADWS_DIR="${REPO_ROOT}/adws"

echo -e "${BLUE}🚀 ADW Webhook Starter${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Cleaning up...${NC}"

    # Kill webhook process if running
    if [ ! -z "$WEBHOOK_PID" ]; then
        kill $WEBHOOK_PID 2>/dev/null || true
    fi

    # Kill ngrok if it was started
    killall ngrok 2>/dev/null || true

    echo -e "${GREEN}✅ Cleanup complete${NC}"
}

# Register cleanup function
trap cleanup EXIT INT TERM

# Check for existing webhook processes
echo -e "${BLUE}Checking for existing webhook processes...${NC}"
if pgrep -f "trigger_webhook.py" > /dev/null; then
    echo -e "${YELLOW}⚠️  Found existing webhook process${NC}"
    echo "   Cleaning up..."
    "${SCRIPT_DIR}/kill_trigger_webhook.sh" > /dev/null 2>&1 || true
    sleep 1
fi

# Load environment variables
if [ -f "${REPO_ROOT}/.env" ]; then
    echo -e "${BLUE}Loading environment variables...${NC}"
    export $(cat "${REPO_ROOT}/.env" | grep -v '^#' | xargs)
fi

# Validate required environment variables
echo -e "${BLUE}Validating environment...${NC}"
MISSING_VARS=""

# Check core requirements
if [ -z "$GITHUB_PAT" ]; then
    MISSING_VARS="${MISSING_VARS} GITHUB_PAT"
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
    MISSING_VARS="${MISSING_VARS} ANTHROPIC_API_KEY"
fi

if [ ! -z "$MISSING_VARS" ]; then
    echo -e "${RED}❌ Missing required environment variables:${NC}${MISSING_VARS}"
    echo "   Please set these in your .env file"
    exit 1
fi

# Determine port
PORT=${PORT:-8001}
if [ ! -z "$1" ] && [[ "$1" =~ ^[0-9]+$ ]]; then
    PORT=$1
    echo -e "${BLUE}Using custom port: ${PORT}${NC}"
fi

# Check if ngrok should be enabled
ENABLE_TUNNEL=false
if [ ! -z "$NGROK_AUTHTOKEN" ]; then
    echo -e "${BLUE}Ngrok auth token detected${NC}"
    ENABLE_TUNNEL=true

    # Check if ngrok is installed
    if ! command -v ngrok &> /dev/null; then
        echo -e "${YELLOW}⚠️  ngrok not installed${NC}"
        echo "   Install with: brew install ngrok (macOS) or snap install ngrok (Linux)"
        ENABLE_TUNNEL=false
    fi
fi

# Build command
CMD="uv run ${ADWS_DIR}/adw_triggers/trigger_webhook.py --port ${PORT}"

if [ "$ENABLE_TUNNEL" = true ]; then
    CMD="${CMD} --tunnel"
    echo -e "${GREEN}✅ Ngrok tunnel will be enabled${NC}"
else
    echo -e "${YELLOW}⚠️  Running in local-only mode (no tunnel)${NC}"
fi

# Start webhook server
echo -e "${BLUE}Starting webhook server...${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Change to ADWS directory
cd "${ADWS_DIR}"

# Start the webhook server
exec $CMD

# Note: exec replaces this script with the webhook process,
# so the cleanup trap will still work when the process is terminated