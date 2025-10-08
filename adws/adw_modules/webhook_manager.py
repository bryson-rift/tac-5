#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic", "requests"]
# ///

"""
GitHub Webhook Manager for ADW

Automatically manages GitHub webhook configuration when ngrok URL changes.
Uses gh CLI for all GitHub operations, matching existing project patterns.
"""

import json
import subprocess
import sys
import os
from typing import Optional, Dict, List, Any

# Handle both module and standalone execution
try:
    from .github import get_repo_url, extract_repo_path, get_github_env
except ImportError:
    # Add parent directory to path for standalone execution
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from adw_modules.github import get_repo_url, extract_repo_path, get_github_env


def list_webhooks(repo_path: str) -> List[Dict[str, Any]]:
    """
    List all webhooks for the repository.

    Args:
        repo_path: Repository path (e.g., "owner/repo")

    Returns:
        List of webhook configurations
    """
    cmd = ["gh", "api", f"repos/{repo_path}/hooks"]
    env = get_github_env()

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        if result.returncode == 0:
            webhooks = json.loads(result.stdout)
            return webhooks
        else:
            print(f"Failed to list webhooks: {result.stderr}")
            return []
    except Exception as e:
        print(f"Error listing webhooks: {e}")
        return []


def find_adw_webhook(repo_path: str) -> Optional[Dict[str, Any]]:
    """
    Find existing ADW webhook by looking for our endpoint pattern.

    Args:
        repo_path: Repository path (e.g., "owner/repo")

    Returns:
        Webhook configuration if found, None otherwise
    """
    webhooks = list_webhooks(repo_path)

    for webhook in webhooks:
        config = webhook.get("config", {})
        url = config.get("url", "")

        # Look for our webhook endpoint pattern
        if "/gh-webhook" in url or "ngrok" in url or webhook.get("name") == "ADW Webhook":
            return webhook

    return None


def create_webhook(repo_path: str, webhook_url: str) -> bool:
    """
    Create a new webhook for ADW.

    Args:
        repo_path: Repository path (e.g., "owner/repo")
        webhook_url: Full webhook URL (e.g., "https://abc.ngrok.io/gh-webhook")

    Returns:
        True if successful, False otherwise
    """
    # Webhook configuration
    config = {
        "name": "web",  # Must be "web" for standard webhooks
        "active": True,
        "events": ["issues", "issue_comment"],
        "config": {
            "url": webhook_url,
            "content_type": "json",
            "insecure_ssl": "1"  # Allow self-signed certs for ngrok
        }
    }

    cmd = [
        "gh", "api",
        f"repos/{repo_path}/hooks",
        "--method", "POST",
        "--input", "-"
    ]

    env = get_github_env()

    try:
        result = subprocess.run(
            cmd,
            input=json.dumps(config),
            capture_output=True,
            text=True,
            env=env
        )

        if result.returncode == 0:
            print(f"✅ Created new webhook: {webhook_url}")
            return True
        else:
            print(f"Failed to create webhook: {result.stderr}")
            return False
    except Exception as e:
        print(f"Error creating webhook: {e}")
        return False


def update_webhook(repo_path: str, webhook_id: int, webhook_url: str) -> bool:
    """
    Update existing webhook with new URL.

    Args:
        repo_path: Repository path (e.g., "owner/repo")
        webhook_id: GitHub webhook ID
        webhook_url: New webhook URL

    Returns:
        True if successful, False otherwise
    """
    # Update configuration
    config = {
        "active": True,
        "config": {
            "url": webhook_url,
            "content_type": "json",
            "insecure_ssl": "1"
        }
    }

    cmd = [
        "gh", "api",
        f"repos/{repo_path}/hooks/{webhook_id}",
        "--method", "PATCH",
        "--input", "-"
    ]

    env = get_github_env()

    try:
        result = subprocess.run(
            cmd,
            input=json.dumps(config),
            capture_output=True,
            text=True,
            env=env
        )

        if result.returncode == 0:
            print(f"✅ Updated webhook #{webhook_id}: {webhook_url}")
            return True
        else:
            print(f"Failed to update webhook: {result.stderr}")
            return False
    except Exception as e:
        print(f"Error updating webhook: {e}")
        return False


def configure_webhook(webhook_url: str) -> bool:
    """
    Main function to configure GitHub webhook.
    Creates new webhook or updates existing one.

    Args:
        webhook_url: Full webhook URL (e.g., "https://abc.ngrok.io/gh-webhook")

    Returns:
        True if successful, False otherwise
    """
    # Get repository information
    try:
        repo_url = get_repo_url()
        repo_path = extract_repo_path(repo_url)
    except Exception as e:
        print(f"❌ Failed to get repository information: {e}")
        return False

    print(f"🔧 Configuring webhook for repository: {repo_path}")

    # Check for existing webhook
    existing = find_adw_webhook(repo_path)

    if existing:
        webhook_id = existing.get("id")
        old_url = existing.get("config", {}).get("url", "")

        if old_url == webhook_url:
            print(f"✅ Webhook already configured with correct URL")
            return True
        else:
            print(f"📝 Updating existing webhook (ID: {webhook_id})")
            print(f"   Old URL: {old_url}")
            print(f"   New URL: {webhook_url}")
            return update_webhook(repo_path, webhook_id, webhook_url)
    else:
        print(f"📝 Creating new webhook")
        return create_webhook(repo_path, webhook_url)


def delete_adw_webhooks(repo_path: Optional[str] = None) -> int:
    """
    Delete all ADW webhooks (useful for cleanup).

    Args:
        repo_path: Repository path, auto-detected if not provided

    Returns:
        Number of webhooks deleted
    """
    if not repo_path:
        try:
            repo_url = get_repo_url()
            repo_path = extract_repo_path(repo_url)
        except Exception as e:
            print(f"Failed to get repository information: {e}")
            return 0

    webhooks = list_webhooks(repo_path)
    deleted = 0

    for webhook in webhooks:
        config = webhook.get("config", {})
        url = config.get("url", "")

        # Delete if it looks like our webhook
        if "/gh-webhook" in url or "ngrok" in url:
            webhook_id = webhook.get("id")
            cmd = [
                "gh", "api",
                f"repos/{repo_path}/hooks/{webhook_id}",
                "--method", "DELETE"
            ]

            env = get_github_env()
            result = subprocess.run(cmd, capture_output=True, text=True, env=env)

            if result.returncode == 0:
                print(f"✅ Deleted webhook #{webhook_id}: {url}")
                deleted += 1
            else:
                print(f"❌ Failed to delete webhook #{webhook_id}")

    return deleted


def test_webhook(webhook_url: str) -> bool:
    """
    Send a test ping to the webhook.

    Args:
        webhook_url: Webhook URL to test

    Returns:
        True if webhook responded successfully
    """
    import requests

    try:
        # Send a ping event
        payload = {
            "zen": "Design for failure.",
            "hook_id": 0,
            "hook": {"type": "Repository", "events": ["issues", "issue_comment"]}
        }

        headers = {
            "X-GitHub-Event": "ping",
            "Content-Type": "application/json"
        }

        response = requests.post(webhook_url, json=payload, headers=headers, timeout=5)

        if response.status_code == 200:
            print(f"✅ Webhook test successful: {webhook_url}")
            return True
        else:
            print(f"❌ Webhook test failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Webhook test error: {e}")
        return False


if __name__ == "__main__":
    # Test webhook management
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            # List all webhooks
            repo_url = get_repo_url()
            repo_path = extract_repo_path(repo_url)
            webhooks = list_webhooks(repo_path)

            print(f"\n📋 Webhooks for {repo_path}:")
            for webhook in webhooks:
                config = webhook.get("config", {})
                print(f"  ID: {webhook.get('id')}")
                print(f"  URL: {config.get('url')}")
                print(f"  Active: {webhook.get('active')}")
                print(f"  Events: {webhook.get('events')}")
                print()

        elif sys.argv[1] == "cleanup":
            # Delete all ADW webhooks
            deleted = delete_adw_webhooks()
            print(f"\n🧹 Deleted {deleted} webhook(s)")

        elif sys.argv[1] == "configure" and len(sys.argv) > 2:
            # Configure webhook with URL
            webhook_url = sys.argv[2]
            success = configure_webhook(webhook_url)
            sys.exit(0 if success else 1)

        else:
            print("Usage:")
            print("  uv run webhook_manager.py list")
            print("  uv run webhook_manager.py cleanup")
            print("  uv run webhook_manager.py configure <webhook_url>")
    else:
        print("Webhook Manager - use 'list', 'cleanup', or 'configure <url>' command")