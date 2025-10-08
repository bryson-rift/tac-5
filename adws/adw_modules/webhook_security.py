"""
GitHub Webhook Security Module

Provides signature validation for GitHub webhooks to ensure requests
are actually from GitHub and haven't been tampered with.
"""

import hmac
import hashlib
from typing import Optional


def validate_github_signature(
    payload_body: bytes,
    signature_header: Optional[str],
    secret: str
) -> bool:
    """
    Validate GitHub webhook signature.

    Args:
        payload_body: Raw request body as bytes
        signature_header: Value of X-Hub-Signature-256 header
        secret: Webhook secret configured in GitHub

    Returns:
        True if signature is valid, False otherwise
    """
    if not signature_header or not secret:
        return False

    # GitHub sends signature as "sha256=<hex_digest>"
    if not signature_header.startswith("sha256="):
        return False

    expected_signature = signature_header[7:]  # Remove "sha256=" prefix

    # Calculate HMAC
    mac = hmac.new(
        secret.encode("utf-8"),
        msg=payload_body,
        digestmod=hashlib.sha256
    )
    calculated_signature = mac.hexdigest()

    # Use constant-time comparison to prevent timing attacks
    return hmac.compare_digest(calculated_signature, expected_signature)


def generate_webhook_secret() -> str:
    """Generate a secure random webhook secret."""
    import secrets
    return secrets.token_hex(32)