#!/usr/bin/env -S uv run
# /// script
# dependencies = ["fastapi", "uvicorn", "python-dotenv", "requests"]
# ///

"""
GitHub Webhook Trigger - AI Developer Workflow (ADW)

FastAPI webhook endpoint that receives GitHub issue events and triggers ADW workflows.
Responds immediately to meet GitHub's 10-second timeout by launching adw_plan_build.py
in the background.

Usage: uv run trigger_webhook.py [--port PORT] [--tunnel]

Environment Requirements:
- PORT: Server port (default: 8001)
- All adw_plan_build.py requirements (GITHUB_PAT, ANTHROPIC_API_KEY, etc.)
"""

import os
import subprocess
import sys
import signal
import argparse
import time
import atexit
from typing import Optional
from fastapi import FastAPI, Request
from dotenv import load_dotenv
import uvicorn

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adw_modules.utils import make_adw_id, setup_logger
from adw_modules.github import make_issue_comment
from adw_modules.workflow_ops import extract_adw_info
from adw_modules.state import ADWState
from adw_modules.port_manager import (
    is_port_in_use,
    kill_process_on_port,
    find_available_port,
    get_port_info
)

# Load environment variables
load_dotenv()

# Parse command line arguments
parser = argparse.ArgumentParser(description="ADW Webhook Trigger Server")
parser.add_argument("--port", "-p", type=int, help="Port to run the server on")
parser.add_argument("--tunnel", action="store_true", help="Enable ngrok tunnel")
args, unknown = parser.parse_known_args()

# Configuration
DEFAULT_PORT = int(os.getenv("PORT", "8001"))
PORT = args.port if args.port else DEFAULT_PORT

# Create FastAPI app
app = FastAPI(title="ADW Webhook Trigger", description="GitHub webhook endpoint for ADW")

# Global variables for server management
webhook_start_time = time.time()
processed_webhooks_count = 0
ngrok_url = None
ngrok_manager = None

def handle_port_conflict(port: int, max_retries: int = 3) -> int:
    """
    Handle port conflicts by attempting to free the port or find an alternative.

    Args:
        port: Desired port number
        max_retries: Maximum attempts to free the port

    Returns:
        Available port number
    """
    if is_port_in_use(port):
        print(f"⚠️  Port {port} is already in use")
        port_info = get_port_info(port)

        if port_info.get("pid"):
            print(f"   Process {port_info['pid']}: {port_info.get('process_name', 'unknown')}")
            print(f"   Attempting to free port {port}...")

            if kill_process_on_port(port, max_retries=max_retries):
                print(f"✅ Successfully freed port {port}")
                time.sleep(1)  # Wait for port to be fully released
                return port
            else:
                print(f"❌ Could not free port {port}")

        # Find alternative port
        print(f"   Looking for alternative port...")
        alternative_port = find_available_port(start_port=port+1, end_port=port+100)

        if alternative_port:
            print(f"✅ Using alternative port: {alternative_port}")
            return alternative_port
        else:
            raise RuntimeError(f"No available ports found near {port}")

    return port

def graceful_shutdown(signum=None, frame=None):
    """Handle graceful shutdown on SIGTERM or SIGINT."""
    print("\n🛑 Shutting down webhook server gracefully...")

    # Cleanup ngrok if running
    if ngrok_manager:
        print("   Closing ngrok tunnel...")
        ngrok_manager.stop_tunnel()

    # Log final stats
    uptime = time.time() - webhook_start_time
    print(f"📊 Server Statistics:")
    print(f"   - Uptime: {uptime:.1f} seconds")
    print(f"   - Webhooks processed: {processed_webhooks_count}")

    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGTERM, graceful_shutdown)
signal.signal(signal.SIGINT, graceful_shutdown)
atexit.register(graceful_shutdown)

# Check and handle port conflicts before starting
try:
    PORT = handle_port_conflict(PORT)
except RuntimeError as e:
    print(f"❌ Failed to start server: {e}")
    sys.exit(1)

print(f"🚀 Starting ADW Webhook Trigger on port {PORT}")

# Setup ngrok tunnel if requested
if args.tunnel or os.getenv("NGROK_AUTHTOKEN"):
    try:
        from ngrok_manager import NgrokManager

        print("🌐 Setting up ngrok tunnel...")
        ngrok_manager = NgrokManager(PORT)

        if ngrok_manager.is_installed() and ngrok_manager.is_configured():
            tunnel_url = ngrok_manager.start_tunnel()
            if tunnel_url:
                ngrok_url = tunnel_url
                webhook_url = ngrok_manager.get_webhook_url()
                print(f"✅ Webhook accessible at: {webhook_url}")
                print(f"   Configure this URL in GitHub webhook settings")
            else:
                print("⚠️  Failed to start ngrok tunnel, continuing with local-only access")
        else:
            if not ngrok_manager.is_installed():
                print("⚠️  ngrok not installed, continuing with local-only access")
            else:
                print("⚠️  ngrok not configured (missing NGROK_AUTHTOKEN), continuing with local-only access")
    except ImportError:
        print("⚠️  ngrok_manager module not found, continuing with local-only access")
    except Exception as e:
        print(f"⚠️  Error setting up ngrok: {e}, continuing with local-only access")

# Bot identifier to prevent webhook loops
ADW_BOT_IDENTIFIER = "[ADW-BOT]"

# Available ADW workflows
AVAILABLE_WORKFLOWS = [
    "adw_plan",
    "adw_build",
    "adw_test", 
    "adw_plan_build",
    "adw_plan_build_test"
]




@app.post("/gh-webhook")
async def github_webhook(request: Request):
    """Handle GitHub webhook events."""
    global processed_webhooks_count
    processed_webhooks_count += 1

    try:
        # Get event type from header
        event_type = request.headers.get("X-GitHub-Event", "")
        
        # Parse webhook payload
        payload = await request.json()
        
        # Extract event details
        action = payload.get("action", "")
        issue = payload.get("issue", {})
        issue_number = issue.get("number")
        
        print(f"Received webhook: event={event_type}, action={action}, issue_number={issue_number}")
        
        workflow = None
        provided_adw_id = None
        trigger_reason = ""
        content_to_check = ""
        
        # Check if this is an issue opened event
        if event_type == "issues" and action == "opened" and issue_number:
            issue_body = issue.get("body", "")
            content_to_check = issue_body
            
            # Check if body contains "adw_" 
            if "adw_" in issue_body.lower():
                # Use temporary ID for classification
                temp_id = make_adw_id()
                workflow, provided_adw_id = extract_adw_info(issue_body, temp_id)
                if workflow:
                    trigger_reason = f"New issue with {workflow} workflow"
        
        # Check if this is an issue comment
        elif event_type == "issue_comment" and action == "created" and issue_number:
            comment = payload.get("comment", {})
            comment_body = comment.get("body", "")
            content_to_check = comment_body
            
            print(f"Comment body: '{comment_body}'")
            
            # Ignore comments from ADW bot to prevent loops
            if ADW_BOT_IDENTIFIER in comment_body:
                print(f"Ignoring ADW bot comment to prevent loop")
                workflow = None
            # Check if comment contains "adw_"
            elif "adw_" in comment_body.lower():
                # Use temporary ID for classification
                temp_id = make_adw_id()
                workflow, provided_adw_id = extract_adw_info(comment_body, temp_id)
                if workflow:
                    trigger_reason = f"Comment with {workflow} workflow"
        
        # Validate workflow constraints
        if workflow == "adw_build" and not provided_adw_id:
            print(f"adw_build requires an adw_id, skipping")
            workflow = None
        
        if workflow:
            # Use provided ADW ID or generate a new one
            adw_id = provided_adw_id or make_adw_id()
            
            # If ADW ID was provided, update/create state file
            if provided_adw_id:
                state = ADWState(provided_adw_id)
                state.update(adw_id=provided_adw_id, issue_number=str(issue_number))
                state.save("webhook_trigger")
            
            # Set up logger
            logger = setup_logger(adw_id, "webhook_trigger")
            logger.info(f"Detected workflow: {workflow} from content: {content_to_check[:100]}...")
            if provided_adw_id:
                logger.info(f"Using provided ADW ID: {provided_adw_id}")
            
            # Post comment to issue about detected workflow
            try:
                make_issue_comment(
                    str(issue_number),
                    f"{ADW_BOT_IDENTIFIER} 🤖 ADW Webhook: Detected `{workflow}` workflow request\n\n"
                    f"Starting workflow with ID: `{adw_id}`\n"
                    f"Reason: {trigger_reason}\n\n"
                    f"Logs will be available at: `agents/{adw_id}/{workflow}/`"
                )
            except Exception as e:
                logger.warning(f"Failed to post issue comment: {e}")
            
            # Build command to run the appropriate workflow  
            script_dir = os.path.dirname(os.path.abspath(__file__))
            adws_dir = os.path.dirname(script_dir)
            repo_root = os.path.dirname(adws_dir)  # Go up to repository root
            trigger_script = os.path.join(adws_dir, f"{workflow}.py")
            
            cmd = ["uv", "run", trigger_script, str(issue_number), adw_id]
            
            print(f"Launching {workflow} for issue #{issue_number}")
            print(f"Command: {' '.join(cmd)} (reason: {trigger_reason})")
            print(f"Working directory: {repo_root}")
            
            # Launch in background using Popen
            process = subprocess.Popen(
                cmd,
                cwd=repo_root,  # Run from repository root where .claude/commands/ is located
                env=os.environ.copy()  # Pass all environment variables
            )
            
            print(f"Background process started for issue #{issue_number} with ADW ID: {adw_id}")
            print(f"Logs will be written to: agents/{adw_id}/{workflow}/execution.log")
            
            # Return immediately
            return {
                "status": "accepted",
                "issue": issue_number,
                "adw_id": adw_id,
                "workflow": workflow,
                "message": f"ADW {workflow} workflow triggered for issue #{issue_number}",
                "reason": trigger_reason,
                "logs": f"agents/{adw_id}/{workflow}/"
            }
        else:
            print(f"Ignoring webhook: event={event_type}, action={action}, issue_number={issue_number}")
            return {
                "status": "ignored",
                "reason": f"Not a triggering event (event={event_type}, action={action})"
            }
            
    except Exception as e:
        print(f"Error processing webhook: {e}")
        # Always return 200 to GitHub to prevent retries
        return {
            "status": "error",
            "message": "Internal error processing webhook"
        }


@app.get("/status")
async def status():
    """Status endpoint showing server metrics and tunnel information."""
    global webhook_start_time, processed_webhooks_count, ngrok_url

    uptime = time.time() - webhook_start_time
    uptime_str = f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m {int(uptime % 60)}s"

    # Get ngrok tunnel status if available
    tunnel_status = None
    if ngrok_manager:
        tunnel_status = ngrok_manager.get_tunnel_status()

    return {
        "status": "running",
        "service": "adw-webhook-trigger",
        "version": "2.0.0",  # Updated version with port management
        "server": {
            "port": PORT,
            "uptime_seconds": int(uptime),
            "uptime": uptime_str,
            "start_time": int(webhook_start_time)
        },
        "metrics": {
            "webhooks_processed": processed_webhooks_count,
            "webhooks_per_minute": round(processed_webhooks_count / (uptime / 60), 2) if uptime > 0 else 0
        },
        "tunnel": {
            "enabled": ngrok_url is not None,
            "url": ngrok_url,
            "webhook_url": f"{ngrok_url}/gh-webhook" if ngrok_url else None,
            "status": tunnel_status
        } if ngrok_manager else {
            "enabled": False,
            "url": None,
            "webhook_url": f"http://localhost:{PORT}/gh-webhook"
        },
        "endpoints": {
            "webhook": "/gh-webhook",
            "health": "/health",
            "status": "/status"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint - runs comprehensive system health check."""
    try:
        # Run the health check script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Health check is in adw_tests, not adw_triggers
        health_check_script = os.path.join(os.path.dirname(script_dir), "adw_tests", "health_check.py")
        
        # Run health check with timeout
        result = subprocess.run(
            ["uv", "run", health_check_script],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.path.dirname(script_dir)  # Run from adws directory
        )
        
        # Print the health check output for debugging
        print("=== Health Check Output ===")
        print(result.stdout)
        if result.stderr:
            print("=== Health Check Errors ===")
            print(result.stderr)
        
        # Parse the output - look for the overall status
        output_lines = result.stdout.strip().split('\n')
        is_healthy = result.returncode == 0
        
        # Extract key information from output
        warnings = []
        errors = []
        
        capturing_warnings = False
        capturing_errors = False
        
        for line in output_lines:
            if "⚠️  Warnings:" in line:
                capturing_warnings = True
                capturing_errors = False
                continue
            elif "❌ Errors:" in line:
                capturing_errors = True
                capturing_warnings = False
                continue
            elif "📝 Next Steps:" in line:
                break
            
            if capturing_warnings and line.strip().startswith("-"):
                warnings.append(line.strip()[2:])
            elif capturing_errors and line.strip().startswith("-"):
                errors.append(line.strip()[2:])
        
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "service": "adw-webhook-trigger",
            "port": PORT,
            "tunnel_url": ngrok_url,
            "webhook_url": f"{ngrok_url}/gh-webhook" if ngrok_url else f"http://localhost:{PORT}/gh-webhook",
            "health_check": {
                "success": is_healthy,
                "warnings": warnings,
                "errors": errors,
                "details": "Run health_check.py directly for full report"
            }
        }
        
    except subprocess.TimeoutExpired:
        return {
            "status": "unhealthy",
            "service": "adw-webhook-trigger",
            "error": "Health check timed out"
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "service": "adw-webhook-trigger",
            "error": f"Health check failed: {str(e)}"
        }


def run_server_with_retry(max_retries: int = 3, retry_delay: int = 5):
    """
    Run the server with automatic retry on failure.

    Args:
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
    """
    global PORT  # Declare global at the beginning of the function

    for attempt in range(max_retries):
        try:
            print(f"\n{'='*50}")
            print(f"Server attempt {attempt + 1}/{max_retries}")
            print(f"{'='*50}\n")

            # Configure uvicorn with logging
            import logging
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(f"{REPO_ROOT}/agents/webhook_server.log"),
                    logging.StreamHandler()
                ]
            )

            print(f"📡 Server starting on http://0.0.0.0:{PORT}")
            print(f"📨 Webhook endpoint: POST /gh-webhook")
            print(f"🏥 Health check: GET /health")
            print(f"📊 Status: GET /status")

            if ngrok_url:
                print(f"🌐 Public webhook URL: {ngrok_url}/gh-webhook")

            print(f"\n{'='*50}")
            print("Server is running. Press Ctrl+C to stop.")
            print(f"{'='*50}\n")

            # Run the server
            uvicorn.run(
                app,
                host="0.0.0.0",
                port=PORT,
                log_level="info",
                access_log=True
            )

            # If we get here, server stopped normally
            break

        except Exception as e:
            print(f"\n❌ Server crashed: {e}")

            if attempt < max_retries - 1:
                print(f"⏳ Restarting in {retry_delay} seconds...")
                time.sleep(retry_delay)

                # Try to cleanup and get a new port if needed
                try:
                    PORT = handle_port_conflict(PORT)
                except Exception as port_error:
                    print(f"❌ Could not resolve port conflict: {port_error}")
            else:
                print(f"❌ Server failed after {max_retries} attempts")
                sys.exit(1)


if __name__ == "__main__":
    # Get repository root for logging
    import os
    REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # Run server with retry logic
    run_server_with_retry()