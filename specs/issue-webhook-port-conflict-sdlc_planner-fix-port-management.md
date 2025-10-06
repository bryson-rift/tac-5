# Chore: Fix Webhook Trigger Port Conflict Issue

## Chore Description
The ADW webhook trigger script (`adws/adw_triggers/trigger_webhook.py`) is experiencing a port binding conflict on port 8001, showing the error "[Errno 48] address already in use". This prevents the webhook listener from starting properly and receiving GitHub webhook events. The issue occurs when a previous instance of the webhook server doesn't shut down cleanly or when multiple instances attempt to start simultaneously. We need to implement robust port management, proper process cleanup, and ngrok integration for the GitHub webhook tunnel.

## Relevant Files
Use these files to resolve the chore:

- `adws/adw_triggers/trigger_webhook.py` - Main webhook listener script that needs port conflict handling
- `scripts/kill_trigger_webhook.sh` - Existing script to kill webhook processes, needs enhancement
- `.env.sample` - Contains ngrok configuration variables that need to be utilized
- `adws/adw_modules/utils.py` - May need utility functions for port checking
- `adws/README.md` - Documentation that should be updated with new port management features

### New Files
- `adws/adw_modules/port_manager.py` - New module for centralized port management utilities
- `scripts/start_webhook.sh` - New script for safely starting webhook with automatic cleanup
- `adws/adw_triggers/ngrok_manager.py` - New module for managing ngrok tunnel integration

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Create Port Management Module
- Create `adws/adw_modules/port_manager.py` with functions to:
  - Check if a port is in use using socket binding test
  - Get PID of process using a specific port
  - Force kill processes on a port with retry logic
  - Find an available port in a range if default is taken
- Include proper error handling and logging
- Add docstrings explaining each function's purpose

### 2. Enhance Webhook Trigger Script with Port Conflict Resolution
- Modify `adws/adw_triggers/trigger_webhook.py` to:
  - Import and use the new port_manager module
  - Check if port 8001 is in use before starting
  - If port is in use, attempt to kill existing process or find alternative port
  - Add command-line argument for custom port: `--port` or `-p`
  - Add graceful shutdown handler for SIGTERM and SIGINT signals
  - Log port binding attempts and successes/failures

### 3. Create Ngrok Integration Module
- Create `adws/adw_triggers/ngrok_manager.py` with functions to:
  - Check if ngrok is installed and configured
  - Start ngrok tunnel on specified port
  - Get public URL from ngrok API
  - Monitor tunnel status
  - Cleanup tunnel on script exit
- Read ngrok configuration from environment variables (NGROK_AUTHTOKEN, NGROK_DOMAIN)

### 4. Update Webhook Script for Ngrok Integration
- Modify `adws/adw_triggers/trigger_webhook.py` to:
  - Add `--tunnel` flag to enable ngrok integration
  - When tunnel flag is set, automatically start ngrok after binding port
  - Display public webhook URL in console output
  - Include tunnel URL in health check response
  - Handle tunnel disconnections gracefully

### 5. Create Safe Start Script
- Create `scripts/start_webhook.sh` that:
  - Checks for existing webhook processes and cleans them up
  - Validates required environment variables
  - Starts webhook with appropriate flags based on .env configuration
  - If NGROK_AUTHTOKEN is present, automatically enables tunnel
  - Displays clear status messages and webhook endpoint URLs
  - Handles interrupt signals to cleanup both webhook and ngrok

### 6. Enhance Kill Script
- Update `scripts/kill_trigger_webhook.sh` to:
  - Kill ngrok processes as well as webhook processes
  - Use the new port_manager utilities for more reliable cleanup
  - Add verbose output option to show what was cleaned up
  - Return appropriate exit codes for scripting

### 7. Add Retry Logic and Health Monitoring
- Modify `adws/adw_triggers/trigger_webhook.py` to:
  - Implement exponential backoff for port binding retries
  - Add `/status` endpoint showing uptime, processed webhooks count, and tunnel status
  - Log all webhook events to a rotating log file
  - Add automatic restart capability if the server crashes

### 8. Update Documentation
- Update `adws/README.md` with:
  - New port management features and how to use them
  - Ngrok integration setup instructions
  - Troubleshooting section for common port conflicts
  - Examples of using the new command-line arguments
  - Best practices for production webhook deployment

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `cd app/server && uv run pytest` - Run server tests to validate the chore is complete with zero regressions
- `./scripts/kill_trigger_webhook.sh` - Should cleanly kill any existing webhook processes
- `cd adws && uv run adw_triggers/trigger_webhook.py --port 8002` - Should start on alternative port
- `cd adws && uv run adw_triggers/trigger_webhook.py` - Should handle port 8001 conflict gracefully
- `./scripts/start_webhook.sh` - Should start webhook with automatic cleanup and ngrok if configured
- `curl http://localhost:8001/health` - Should return healthy status with port and tunnel information
- `curl http://localhost:8001/status` - Should show server status and metrics
- `cd adws && uv run adw_tests/health_check.py` - ADW health check should pass

## Notes
- The port conflict is likely caused by ungraceful shutdowns leaving orphaned processes
- Using lsof and fuser commands can help identify processes holding ports
- Ngrok free tier has limitations on concurrent tunnels and custom domains
- Consider implementing a webhook queue system for high-volume scenarios
- The health and status endpoints will help with monitoring in production
- Alternative to ngrok: Cloudflare Tunnel (if CLOUDFLARED_TUNNEL_TOKEN is configured)
- For production, consider using a reverse proxy like nginx with proper SSL termination