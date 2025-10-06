"""
Ngrok Tunnel Manager

This module handles ngrok tunnel integration for exposing local webhook endpoints
to the internet, enabling GitHub webhooks to reach the local development server.
"""

import os
import subprocess
import json
import time
import requests
import signal
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class NgrokManager:
    """Manages ngrok tunnel lifecycle and configuration."""

    def __init__(self, port: int, authtoken: Optional[str] = None, domain: Optional[str] = None):
        """
        Initialize NgrokManager.

        Args:
            port: Local port to tunnel
            authtoken: Ngrok authentication token (or from env NGROK_AUTHTOKEN)
            domain: Custom ngrok domain (or from env NGROK_DOMAIN)
        """
        self.port = port
        self.authtoken = authtoken or os.getenv("NGROK_AUTHTOKEN")
        self.domain = domain or os.getenv("NGROK_DOMAIN")
        self.process = None
        self.tunnel_url = None
        self.api_url = "http://localhost:4040/api"  # Ngrok local API

    def is_installed(self) -> bool:
        """Check if ngrok is installed and available."""
        try:
            result = subprocess.run(
                ["ngrok", "version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def is_configured(self) -> bool:
        """Check if ngrok is properly configured with auth token."""
        if not self.authtoken:
            logger.warning("No NGROK_AUTHTOKEN found in environment")
            return False
        return True

    def start_tunnel(self, protocol: str = "http") -> Optional[str]:
        """
        Start ngrok tunnel for the specified port.

        Args:
            protocol: Protocol to use (http or https)

        Returns:
            Public tunnel URL if successful, None otherwise
        """
        if not self.is_installed():
            logger.error("ngrok is not installed. Please install it first.")
            return None

        if not self.is_configured():
            logger.error("ngrok is not configured. Please set NGROK_AUTHTOKEN.")
            return None

        try:
            # Kill any existing ngrok processes
            self.cleanup_existing_tunnels()

            # Build ngrok command
            cmd = ["ngrok", protocol, str(self.port)]

            # Add auth token if provided
            if self.authtoken:
                cmd.extend(["--authtoken", self.authtoken])

            # Add custom domain if provided
            if self.domain:
                cmd.extend(["--domain", self.domain])

            # Add other useful options
            cmd.extend([
                "--log", "stdout",
                "--log-format", "json",
                "--log-level", "info"
            ])

            logger.info(f"Starting ngrok tunnel on port {self.port}...")

            # Start ngrok process
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Wait for tunnel to be established
            time.sleep(3)

            # Get tunnel URL from API
            self.tunnel_url = self.get_tunnel_url()

            if self.tunnel_url:
                logger.info(f"✅ Ngrok tunnel established: {self.tunnel_url}")
                return self.tunnel_url
            else:
                logger.error("Failed to get tunnel URL from ngrok")
                self.stop_tunnel()
                return None

        except Exception as e:
            logger.error(f"Error starting ngrok tunnel: {e}")
            self.stop_tunnel()
            return None

    def get_tunnel_url(self) -> Optional[str]:
        """
        Get the public URL of the active tunnel from ngrok API.

        Returns:
            Public tunnel URL or None if not found
        """
        max_retries = 10
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                # Query ngrok API for tunnel information
                response = requests.get(f"{self.api_url}/tunnels", timeout=2)

                if response.status_code == 200:
                    data = response.json()
                    tunnels = data.get("tunnels", [])

                    for tunnel in tunnels:
                        if tunnel.get("proto") in ["http", "https"]:
                            public_url = tunnel.get("public_url")
                            if public_url:
                                # Prefer HTTPS URL
                                if public_url.startswith("https://"):
                                    return public_url
                                # Store HTTP URL but keep looking for HTTPS
                                elif not self.tunnel_url:
                                    self.tunnel_url = public_url

                    if self.tunnel_url:
                        return self.tunnel_url

            except requests.exceptions.RequestException as e:
                logger.debug(f"Attempt {attempt + 1}: Cannot reach ngrok API: {e}")

            # Wait before retrying
            if attempt < max_retries - 1:
                time.sleep(retry_delay)

        return None

    def get_tunnel_status(self) -> Dict[str, Any]:
        """
        Get detailed status of the active tunnel.

        Returns:
            Dictionary with tunnel status information
        """
        status = {
            "active": False,
            "url": None,
            "port": self.port,
            "metrics": {}
        }

        try:
            # Check if process is running
            if self.process and self.process.poll() is None:
                status["active"] = True
                status["url"] = self.tunnel_url

                # Get metrics from API
                try:
                    response = requests.get(f"{self.api_url}/metrics", timeout=2)
                    if response.status_code == 200:
                        metrics = response.json()
                        status["metrics"] = {
                            "connections": metrics.get("connections", 0),
                            "http_requests": metrics.get("http", {}).get("count", 0)
                        }
                except:
                    pass

        except Exception as e:
            logger.error(f"Error getting tunnel status: {e}")

        return status

    def monitor_tunnel(self, callback=None):
        """
        Monitor tunnel status and reconnect if disconnected.

        Args:
            callback: Optional callback function to call with status updates
        """
        while self.process and self.process.poll() is None:
            status = self.get_tunnel_status()

            if callback:
                callback(status)

            if not status["active"]:
                logger.warning("Tunnel disconnected, attempting to reconnect...")
                self.stop_tunnel()
                self.start_tunnel()

            time.sleep(10)  # Check every 10 seconds

    def stop_tunnel(self):
        """Stop the ngrok tunnel."""
        if self.process:
            try:
                logger.info("Stopping ngrok tunnel...")
                self.process.terminate()

                # Wait for graceful shutdown
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if needed
                    self.process.kill()
                    self.process.wait()

                self.process = None
                self.tunnel_url = None
                logger.info("✅ Ngrok tunnel stopped")

            except Exception as e:
                logger.error(f"Error stopping ngrok tunnel: {e}")

    def cleanup_existing_tunnels(self):
        """Kill any existing ngrok processes."""
        try:
            # Kill ngrok processes
            if os.name == "posix":  # Unix/Linux/Mac
                subprocess.run(["killall", "ngrok"], capture_output=True)
            else:  # Windows
                subprocess.run(["taskkill", "/F", "/IM", "ngrok.exe"], capture_output=True)

            time.sleep(1)  # Wait for processes to terminate

        except Exception as e:
            logger.debug(f"No existing ngrok processes to clean up: {e}")

    def get_webhook_url(self, path: str = "/gh-webhook") -> Optional[str]:
        """
        Get the full webhook URL including the path.

        Args:
            path: Webhook endpoint path

        Returns:
            Full webhook URL or None if tunnel not active
        """
        if self.tunnel_url:
            return f"{self.tunnel_url}{path}"
        return None

    def __enter__(self):
        """Context manager entry."""
        self.start_tunnel()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_tunnel()


def check_ngrok_installation() -> bool:
    """
    Check if ngrok is installed and provide installation instructions if not.

    Returns:
        True if installed, False otherwise
    """
    manager = NgrokManager(port=8000)  # Port doesn't matter for this check

    if manager.is_installed():
        return True

    print("❌ ngrok is not installed")
    print("\nTo install ngrok:")
    print("  macOS:   brew install ngrok")
    print("  Ubuntu:  snap install ngrok")
    print("  Windows: choco install ngrok")
    print("\nOr download from: https://ngrok.com/download")

    return False


def setup_ngrok_auth(authtoken: str) -> bool:
    """
    Configure ngrok with authentication token.

    Args:
        authtoken: Ngrok authentication token

    Returns:
        True if successful, False otherwise
    """
    try:
        result = subprocess.run(
            ["ngrok", "config", "add-authtoken", authtoken],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Failed to set ngrok authtoken: {e}")
        return False