#!/bin/bash
# Start webhook server with ngrok tunnel

echo "🚀 Starting ADW Webhook with Ngrok Tunnel"
echo "=========================================="

# Set working directory
cd "$(dirname "$0")/adws" || exit 1

# Export the ngrok auth token from .env.sample (you should move this to .env)
export NGROK_AUTHTOKEN="33hWwtWqMVDs7gLtHPh8we7kV4w_7NjB7zZJ9XX5vfxaXJURy"

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok is not installed"
    echo "Install with: brew install ngrok"
    exit 1
fi

echo "✅ ngrok is installed"
echo "📝 Using NGROK_AUTHTOKEN: ${NGROK_AUTHTOKEN:0:10}..."

# Kill any existing webhook processes
echo "🧹 Cleaning up existing processes..."
killall -q ngrok 2>/dev/null
lsof -ti:8001 | xargs kill -9 2>/dev/null

# Give processes time to clean up
sleep 2

echo ""
echo "Starting webhook server with tunnel..."
echo "Once started, you'll see a public URL like:"
echo "  https://abc123.ngrok-free.app/gh-webhook"
echo ""
echo "Use that URL in GitHub webhook settings!"
echo "=========================================="
echo ""

# Run the webhook with tunnel flag
uv run adw_triggers/trigger_webhook.py --tunnel