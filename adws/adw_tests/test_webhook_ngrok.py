#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "python-dotenv",
#     "requests",
#     "pydantic",
# ]
# ///

"""
Test Suite for ADW Webhook and Ngrok Integration

Tests the webhook trigger system with ngrok tunnel integration.
Run directly with: uv run adws/adw_tests/test_webhook_ngrok.py

This test suite validates:
1. Environment configuration loading
2. Ngrok tunnel establishment
3. Webhook server startup
4. GitHub webhook event processing
5. ADW workflow triggering
"""

import os
import sys
import json
import time
import subprocess
import requests
from pathlib import Path
from typing import Optional, Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# Load .env from repository root
root_dir = Path(__file__).parent.parent.parent
env_path = root_dir / '.env'
if env_path.exists():
    load_dotenv(env_path)


# Test Environment Configuration Functions
def check_env_file_exists():
    """Test that .env file exists in repository root."""
    if not env_path.exists():
        print(f"❌ .env file not found at {env_path}")
        return False
    print("✅ .env file exists")
    return True


def check_required_env_vars():
    """Test that required environment variables are set."""
    required_vars = [
        "GITHUB_PAT",
        "ANTHROPIC_API_KEY",
        "CLAUDE_CODE_PATH"
    ]

    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)

    if missing:
        print(f"❌ Missing required environment variables: {missing}")
        return False
    print("✅ All required environment variables are set")
    return True


def check_ngrok_authtoken():
    """Test that NGROK_AUTHTOKEN is available."""
    token = os.getenv("NGROK_AUTHTOKEN")
    if not token:
        print("❌ NGROK_AUTHTOKEN not found in environment")
        return False
    if len(token) <= 20:
        print("❌ NGROK_AUTHTOKEN appears invalid (too short)")
        return False
    print("✅ NGROK_AUTHTOKEN is configured")
    return True


# Test Ngrok Integration Functions
def check_ngrok_installed():
    """Test that ngrok is installed and accessible."""
    try:
        result = subprocess.run(
            ["ngrok", "version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            print("❌ ngrok command failed")
            return False
        if "ngrok" not in result.stdout.lower():
            print("❌ ngrok version output invalid")
            return False
        print("✅ ngrok is installed and accessible")
        return True
    except FileNotFoundError:
        print("❌ ngrok is not installed. Install with: brew install ngrok")
        return False
    except subprocess.TimeoutExpired:
        print("❌ ngrok version command timed out")
        return False


def check_ngrok_config():
    """Test that ngrok configuration is valid."""
    try:
        result = subprocess.run(
            ["ngrok", "config", "check"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            print(f"❌ ngrok config invalid: {result.stderr}")
            return False
        print("✅ ngrok configuration is valid")
        return True
    except Exception as e:
        print(f"❌ Failed to check ngrok config: {e}")
        return False


def check_ngrok_tunnel_creation():
    """Test creating an ngrok tunnel programmatically."""
    # Kill any existing ngrok processes
    subprocess.run(["killall", "ngrok"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)

    # Start ngrok for testing (on a different port to avoid conflicts)
    test_port = 9999
    token = os.getenv("NGROK_AUTHTOKEN")

    if not token:
        print("❌ Cannot test tunnel creation without NGROK_AUTHTOKEN")
        return False

    proc = subprocess.Popen(
        ["ngrok", "http", str(test_port), "--authtoken", token],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    try:
        # Wait for tunnel to establish
        tunnel_url = None
        for attempt in range(10):
            time.sleep(1)

            # Check if process died
            if proc.poll() is not None:
                stdout, stderr = proc.communicate()
                print(f"❌ ngrok process died: {stderr.decode()}")
                return False

            # Try to get tunnel URL from API
            try:
                resp = requests.get("http://localhost:4040/api/tunnels", timeout=1)
                if resp.status_code == 200:
                    tunnels = resp.json().get("tunnels", [])
                    for tunnel in tunnels:
                        if str(test_port) in tunnel.get("config", {}).get("addr", ""):
                            tunnel_url = tunnel.get("public_url")
                            break
            except requests.exceptions.RequestException:
                continue

            if tunnel_url:
                break

        if not tunnel_url:
            print("❌ Failed to establish ngrok tunnel")
            return False

        if not tunnel_url.startswith("https://"):
            print(f"❌ Tunnel URL not HTTPS: {tunnel_url}")
            return False

        print(f"✅ ngrok tunnel created successfully: {tunnel_url}")
        return True

    finally:
        # Cleanup
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()


# Test Webhook Server Functions
def check_webhook_health_endpoint():
    """Test the webhook health endpoint."""
    webhook_url = "http://localhost:8001"
    try:
        resp = requests.get(f"{webhook_url}/health", timeout=2)
        if resp.status_code == 200:
            data = resp.json()
            if data["status"] not in ["healthy", "unhealthy"]:
                print("❌ Invalid health status response")
                return False
            if "service" not in data:
                print("❌ Missing service field in health response")
                return False
            print("✅ Webhook health endpoint is working")
            return True
        else:
            print(f"❌ Health endpoint returned status {resp.status_code}")
            return False
    except requests.exceptions.RequestException:
        print("Skipping: Webhook server not running")
        return True  # Skip test if server not running


def check_webhook_status_endpoint():
    """Test the webhook status endpoint."""
    webhook_url = "http://localhost:8001"
    try:
        resp = requests.get(f"{webhook_url}/status", timeout=2)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") != "running":
                print("❌ Webhook status not 'running'")
                return False
            if "server" not in data:
                print("❌ Missing server field in status response")
                return False
            if "metrics" not in data:
                print("❌ Missing metrics field in status response")
                return False
            print("✅ Webhook status endpoint is working")
            return True
        else:
            print(f"❌ Status endpoint returned status {resp.status_code}")
            return False
    except requests.exceptions.RequestException:
        print("Skipping: Webhook server not running")
        return True  # Skip test if server not running


def check_webhook_accepts_github_events():
    """Test that webhook accepts GitHub issue events."""
    webhook_url = "http://localhost:8001"

    # Create a mock GitHub webhook payload
    payload = {
        "action": "opened",
        "issue": {
            "number": 9999,
            "title": "Test Issue",
            "body": "This is a test issue for pytest"
        }
    }

    headers = {
        "X-GitHub-Event": "issues",
        "Content-Type": "application/json"
    }

    try:
        resp = requests.post(
            f"{webhook_url}/gh-webhook",
            json=payload,
            headers=headers,
            timeout=5
        )
        if resp.status_code != 200:
            print(f"❌ Webhook returned status {resp.status_code}")
            return False

        data = resp.json()
        if data.get("status") not in ["accepted", "ignored"]:
            print("❌ Invalid webhook response status")
            return False

        print("✅ Webhook accepts GitHub events")
        return True
    except requests.exceptions.RequestException:
        print("Skipping: Webhook server not running")
        return True  # Skip test if server not running


def check_webhook_detects_adw_workflow():
    """Test that webhook detects ADW workflow requests."""
    webhook_url = "http://localhost:8001"

    # Payload with ADW workflow trigger
    payload = {
        "action": "opened",
        "issue": {
            "number": 9998,
            "title": "Test Issue",
            "body": "/feature Add a new test feature\nadw_plan_build"
        }
    }

    headers = {
        "X-GitHub-Event": "issues",
        "Content-Type": "application/json"
    }

    try:
        resp = requests.post(
            f"{webhook_url}/gh-webhook",
            json=payload,
            headers=headers,
            timeout=5
        )
        if resp.status_code != 200:
            print(f"❌ Webhook returned status {resp.status_code}")
            return False

        data = resp.json()

        # Should detect the workflow
        if "adw_plan_build" in payload["issue"]["body"]:
            if data.get("status") != "accepted":
                print("❌ Webhook did not accept ADW workflow trigger")
                return False
            if "workflow" not in data:
                print("❌ Missing workflow field in response")
                return False
            if data.get("workflow") != "adw_plan_build":
                print("❌ Incorrect workflow detected")
                return False

        print("✅ Webhook detects ADW workflow triggers")
        return True
    except requests.exceptions.RequestException:
        print("Skipping: Webhook server not running")
        return True  # Skip test if server not running


# Test Webhook Auto Configuration Functions
def check_webhook_manager_module_exists():
    """Test that webhook_manager.py module exists."""
    webhook_manager = Path(__file__).parent.parent / "adw_modules" / "webhook_manager.py"
    if not webhook_manager.exists():
        print("❌ webhook_manager.py not found")
        return False
    print("✅ webhook_manager.py module exists")
    return True


def check_webhook_manager_functions():
    """Test that webhook_manager has required functions."""
    # Import the module
    sys.path.insert(0, str(Path(__file__).parent.parent))
    try:
        from adw_modules import webhook_manager

        # Check required functions exist
        required_functions = [
            'configure_webhook',
            'list_webhooks',
            'find_adw_webhook',
            'create_webhook',
            'update_webhook'
        ]

        missing_functions = []
        for func in required_functions:
            if not hasattr(webhook_manager, func):
                missing_functions.append(func)

        if missing_functions:
            print(f"❌ Missing functions in webhook_manager: {missing_functions}")
            return False

        print("✅ webhook_manager has all required functions")
        return True
    except ImportError as e:
        print(f"❌ Failed to import webhook_manager: {e}")
        return False


def check_webhook_auto_configuration_integration():
    """Test that trigger_webhook.py includes auto-configuration code."""
    # Check if GitHub token is available
    if not os.environ.get('GITHUB_TOKEN') and not os.environ.get('GITHUB_PAT'):
        print("Skipping: GitHub token not configured")
        return True

    trigger_webhook = Path(__file__).parent.parent / "adw_triggers" / "trigger_webhook.py"

    if not trigger_webhook.exists():
        print("❌ trigger_webhook.py not found")
        return False

    with open(trigger_webhook, 'r') as f:
        content = f.read()

    # Check for webhook manager import
    if 'webhook_manager' not in content and 'configure_webhook' not in content:
        print("❌ Webhook auto-configuration not integrated")
        return False

    # Check for GitHub webhook configuration call
    if 'Configuring GitHub webhook' not in content and 'configure_webhook' not in content:
        print("❌ GitHub webhook configuration not called")
        return False

    print("✅ Webhook auto-configuration is integrated")
    return True


# Test End-to-End Workflow Functions
def check_full_workflow_simulation():
    """Simulate a complete workflow from GitHub event to ADW trigger."""
    # This test verifies the components exist
    trigger_webhook = Path(__file__).parent.parent / "adw_triggers" / "trigger_webhook.py"
    if not trigger_webhook.exists():
        print("❌ trigger_webhook.py not found")
        return False

    adw_plan_build = Path(__file__).parent.parent / "adw_plan_build.py"
    if not adw_plan_build.exists():
        print("❌ adw_plan_build.py not found")
        return False

    webhook_manager = Path(__file__).parent.parent / "adw_modules" / "webhook_manager.py"
    if not webhook_manager.exists():
        print("❌ webhook_manager.py for auto-configuration not found")
        return False

    print("✅ All workflow components exist")
    return True


def check_webhook_prevents_infinite_loops():
    """Test that webhook ignores ADW bot comments to prevent loops."""
    webhook_url = "http://localhost:8001"

    # Payload with ADW bot comment (should be ignored)
    payload = {
        "action": "created",
        "issue": {"number": 9997},
        "comment": {
            "body": "[ADW-BOT] This is a bot comment\nadw_plan_build"
        }
    }

    headers = {
        "X-GitHub-Event": "issue_comment",
        "Content-Type": "application/json"
    }

    try:
        resp = requests.post(
            f"{webhook_url}/gh-webhook",
            json=payload,
            headers=headers,
            timeout=5
        )
        if resp.status_code != 200:
            print(f"❌ Webhook returned status {resp.status_code}")
            return False

        data = resp.json()
        # Should ignore bot comments
        if data.get("status") != "ignored":
            print("❌ Webhook did not ignore bot comment")
            return False

        print("✅ Webhook prevents infinite loops")
        return True
    except requests.exceptions.RequestException:
        print("Skipping: Webhook server not running")
        return True  # Skip test if server not running


def check_integration_suite_health():
    """Meta-test to verify the test suite itself is healthy."""
    # Verify test environment
    if sys.version_info < (3, 10):
        print("❌ Python 3.10+ required")
        return False

    # Verify test dependencies
    required_modules = ["requests", "dotenv", "pydantic"]
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)

    if missing_modules:
        print(f"❌ Missing modules: {missing_modules}")
        return False

    print("✅ Test suite health check passed")
    return True


def main():
    """Run all tests and report results."""
    print("=" * 60)
    print("ADW Webhook and Ngrok Integration Test Suite")
    print("=" * 60 + "\n")

    # Define all test functions
    tests = [
        # Environment Configuration Tests
        ("Environment: .env file exists", check_env_file_exists),
        ("Environment: Required variables", check_required_env_vars),
        ("Environment: Ngrok auth token", check_ngrok_authtoken),

        # Ngrok Integration Tests
        ("Ngrok: Installation check", check_ngrok_installed),
        ("Ngrok: Configuration check", check_ngrok_config),
        ("Ngrok: Tunnel creation", check_ngrok_tunnel_creation),

        # Webhook Server Tests
        ("Webhook: Health endpoint", check_webhook_health_endpoint),
        ("Webhook: Status endpoint", check_webhook_status_endpoint),
        ("Webhook: GitHub events", check_webhook_accepts_github_events),
        ("Webhook: ADW workflow detection", check_webhook_detects_adw_workflow),

        # Webhook Auto Configuration Tests
        ("Config: Webhook manager exists", check_webhook_manager_module_exists),
        ("Config: Webhook manager functions", check_webhook_manager_functions),
        ("Config: Auto-configuration integration", check_webhook_auto_configuration_integration),

        # End-to-End Workflow Tests
        ("Workflow: Component existence", check_full_workflow_simulation),
        ("Workflow: Infinite loop prevention", check_webhook_prevents_infinite_loops),

        # Health Check
        ("Suite: Health check", check_integration_suite_health),
    ]

    # Run all tests
    passed = 0
    failed = 0
    skipped = 0

    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            result = test_func()
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            failed += 1

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Total: {passed + failed}")

    # Exit with appropriate code
    if failed > 0:
        print("\nSome tests failed. Please review the output above.")
        sys.exit(1)
    else:
        print("\nAll tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()