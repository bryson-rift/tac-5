#!/usr/bin/env python3
"""Test ngrok tunnel setup independently"""

import os
import sys
import subprocess
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Check if ngrok is installed
result = subprocess.run(["which", "ngrok"], capture_output=True, text=True)
if result.returncode != 0:
    print("❌ ngrok is not installed")
    print("Install with: brew install ngrok")
    sys.exit(1)

print("✅ ngrok is installed at:", result.stdout.strip())

# Check if ngrok is configured
result = subprocess.run(["ngrok", "config", "check"], capture_output=True, text=True)
print("✅ ngrok config:", result.stdout.strip())

# Set the auth token from .env.sample (for testing)
NGROK_AUTHTOKEN = "33hWwtWqMVDs7gLtHPh8we7kV4w_7NjB7zZJ9XX5vfxaXJURy"
print(f"📝 Using NGROK_AUTHTOKEN: {NGROK_AUTHTOKEN[:10]}...")

# Start a simple test tunnel
print("\n🚀 Starting test tunnel on port 8001...")
print("This will open ngrok on port 8001 for testing")
print("Press Ctrl+C to stop\n")

# Start ngrok with the auth token
try:
    subprocess.run([
        "ngrok", "http", "8001",
        "--authtoken", NGROK_AUTHTOKEN,
        "--log", "stdout"
    ])
except KeyboardInterrupt:
    print("\n✅ Test complete!")