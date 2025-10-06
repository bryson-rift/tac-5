#!/bin/bash

# Enhanced Kill Script for ADW Webhook Trigger
# Kills webhook processes, ngrok tunnels, and cleans up ports

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
ADWS_DIR="${REPO_ROOT}/adws"

# Add ADWS modules to Python path
export PYTHONPATH="${ADWS_DIR}:${PYTHONPATH}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
VERBOSE=false
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        *)
            shift
            ;;
    esac
done

echo -e "${BLUE}ADW Webhook Cleanup${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━"

CLEANED_COUNT=0

# Kill webhook processes
echo -e "${BLUE}Stopping webhook processes...${NC}"
WEBHOOK_PIDS=$(pgrep -f "trigger_webhook.py" 2>/dev/null)
if [ ! -z "$WEBHOOK_PIDS" ]; then
    for PID in $WEBHOOK_PIDS; do
        if [ "$VERBOSE" = true ]; then
            PROCESS_INFO=$(ps -p $PID -o command= 2>/dev/null || echo "Unknown process")
            echo -e "  Killing PID ${PID}: ${PROCESS_INFO:0:60}..."
        fi
        kill $PID 2>/dev/null || kill -9 $PID 2>/dev/null
        ((CLEANED_COUNT++))
    done
    echo -e "${GREEN}✅ Stopped ${CLEANED_COUNT} webhook process(es)${NC}"
else
    echo -e "${YELLOW}⚠️  No webhook processes found${NC}"
fi

# Kill ngrok processes
echo -e "${BLUE}Stopping ngrok tunnels...${NC}"
NGROK_COUNT=0
if pgrep -x "ngrok" > /dev/null 2>&1; then
    if [ "$VERBOSE" = true ]; then
        NGROK_PIDS=$(pgrep -x "ngrok")
        for PID in $NGROK_PIDS; do
            echo -e "  Killing ngrok PID ${PID}"
        done
    fi
    pkill -x "ngrok" 2>/dev/null || killall ngrok 2>/dev/null
    NGROK_COUNT=$(pgrep -x "ngrok" 2>/dev/null | wc -l)
    if [ $NGROK_COUNT -eq 0 ]; then
        echo -e "${GREEN}✅ Stopped ngrok tunnel(s)${NC}"
        ((CLEANED_COUNT++))
    fi
else
    echo -e "${YELLOW}⚠️  No ngrok processes found${NC}"
fi

# Clean up ports using Python port_manager
echo -e "${BLUE}Cleaning up ports...${NC}"

# Default webhook port
PORT=${PORT:-8001}

# Use Python to check and clean ports
python3 - <<EOF 2>/dev/null
import sys
import os
sys.path.insert(0, "${ADWS_DIR}")

try:
    from adw_modules.port_manager import is_port_in_use, kill_process_on_port, get_port_info

    ports_to_check = [8001, 8002, 8000]  # Common webhook ports
    cleaned = 0

    for port in ports_to_check:
        if is_port_in_use(port):
            info = get_port_info(port)
            if $VERBOSE:
                print(f"  Port {port} in use by PID {info.get('pid', 'unknown')}")

            if kill_process_on_port(port, force=True):
                print(f"  ✅ Freed port {port}")
                cleaned += 1

    if cleaned > 0:
        print(f"✅ Cleaned {cleaned} port(s)")
    else:
        print("  No ports needed cleaning")

except Exception as e:
    # Fallback to shell commands if Python module not available
    import subprocess
    subprocess.run(["lsof", "-ti", ":8001"], capture_output=True)

EOF

# If Python cleanup failed, use fallback method
if [ $? -ne 0 ]; then
    if [ "$VERBOSE" = true ]; then
        echo "  Using fallback port cleanup method..."
    fi

    for PORT in 8001 8002 8000; do
        if lsof -i :$PORT > /dev/null 2>&1; then
            lsof -ti :$PORT | xargs kill -9 2>/dev/null
            echo -e "${GREEN}✅ Freed port $PORT${NC}"
            ((CLEANED_COUNT++))
        fi
    done
fi

# Clean up any zombie Python processes related to ADW
echo -e "${BLUE}Checking for zombie processes...${NC}"
ZOMBIE_COUNT=0
ZOMBIE_PIDS=$(ps aux | grep -E "python.*adw_" | grep -v grep | awk '{print $2}' 2>/dev/null)
if [ ! -z "$ZOMBIE_PIDS" ]; then
    for PID in $ZOMBIE_PIDS; do
        if [ "$VERBOSE" = true ]; then
            PROCESS_INFO=$(ps -p $PID -o command= 2>/dev/null || echo "Unknown")
            echo -e "  Cleaning zombie PID ${PID}: ${PROCESS_INFO:0:60}..."
        fi
        kill $PID 2>/dev/null || kill -9 $PID 2>/dev/null
        ((ZOMBIE_COUNT++))
    done
    if [ $ZOMBIE_COUNT -gt 0 ]; then
        echo -e "${GREEN}✅ Cleaned ${ZOMBIE_COUNT} zombie process(es)${NC}"
        ((CLEANED_COUNT+=ZOMBIE_COUNT))
    fi
else
    echo -e "  No zombie processes found"
fi

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $CLEANED_COUNT -gt 0 ]; then
    echo -e "${GREEN}✅ Cleanup complete: ${CLEANED_COUNT} item(s) cleaned${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  Nothing to clean${NC}"
    exit 0
fi