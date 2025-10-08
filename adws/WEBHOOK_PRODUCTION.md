# ADW Webhook Production Deployment Guide

## Overview

This guide covers **production deployment** options for the ADW webhook system. For basic development setup with ngrok, see the main [README.md](README.md#deploy-webhook-for-instant-response).

The ADW webhook system receives GitHub events and triggers automated development workflows.

## Critical Assumptions & Requirements

### Environment Setup
1. **Working Directory**: Scripts assume they run from `adws/` directory
2. **Python Version**: Requires Python 3.10+ (tested on 3.12-3.13)
3. **Environment Variables**: Must be in `.env` at repository root
4. **Dependencies**: Managed via `uv` with inline script dependencies

### Required Environment Variables
```bash
# Required for ADW operations
GITHUB_PAT=ghp_xxxx                # GitHub Personal Access Token
ANTHROPIC_API_KEY=sk-ant-xxx       # Anthropic API for Claude
CLAUDE_CODE_PATH=/path/to/claude   # Path to Claude CLI

# Required for ngrok tunnel (development)
NGROK_AUTHTOKEN=xxx                # From https://dashboard.ngrok.com

# Recommended for security (not yet implemented)
GITHUB_WEBHOOK_SECRET=xxx          # Shared secret with GitHub
```

## Development Setup (Ngrok)

### Quick Start
```bash
cd adws
uv run adw_triggers/trigger_webhook.py --tunnel
```

### What Happens (Automatic Configuration)
1. Loads `.env` from repository root
2. Validates NGROK_AUTHTOKEN exists
3. Kills any existing ngrok processes
4. Starts ngrok tunnel on port 8001
5. Displays public webhook URL
6. **Automatically configures GitHub webhook** using `webhook_manager.py`
7. Starts FastAPI server with health monitoring

### Auto-Configuration Details
The system automatically handles webhook configuration:
- Uses `gh` CLI to interact with GitHub API
- Checks for existing ADW webhooks
- Updates webhook URL if one exists
- Creates new webhook if none exists
- Configures proper events (issues, issue_comments)
- No manual GitHub settings required!

### Manual Configuration (Optional)
If auto-configuration fails, manually configure:
1. Copy the ngrok URL (e.g., `https://abc123.ngrok-free.dev/gh-webhook`)
2. Go to GitHub repo → Settings → Webhooks
3. Add webhook with:
   - Payload URL: `<ngrok_url>/gh-webhook`
   - Content type: `application/json`
   - Events: Issues, Issue comments
   - Active: ✓

## Production Deployment Options

### Option 1: Cloudflare Tunnel (Recommended)
```bash
# Install cloudflared
brew install cloudflared

# Authenticate
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create adw-webhook

# Run webhook with tunnel
cloudflared tunnel run --url http://localhost:8001 adw-webhook
```

### Option 2: Direct Internet Exposure
**Requirements**:
- Public IP address
- SSL certificate (Let's Encrypt)
- Reverse proxy (nginx/caddy)
- Firewall configuration

**Example Nginx Config**:
```nginx
server {
    listen 443 ssl;
    server_name webhook.yourcompany.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location /gh-webhook {
        proxy_pass http://localhost:8001;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### Option 3: GitHub App
Create a GitHub App for production use:
- More secure (automatic webhook secret)
- Higher rate limits
- Installation-wide access
- Automatic webhook management

## Current Limitations & TODOs

### Security Issues
- [x] **Webhook signature validation module exists** (`webhook_security.py`) - Not yet integrated into webhook endpoint
- [ ] No rate limiting implementation
- [ ] No request size limits
- [ ] Secrets in .env file (should use secret manager)
- [ ] Webhook secret not automatically configured in GitHub

### Stability Issues
- [x] **Automatic webhook URL update on restart** - webhook_manager.py handles URL changes
- [ ] Ngrok URL changes on restart (need reserved domain for consistency)
- [ ] No automatic reconnection on failure
- [ ] No persistent state across restarts
- [ ] No queueing for webhook events

### Operational Issues
- [x] **Port conflict resolution** - Automatic port management with alternatives
- [x] **Health check endpoint** - `/health` endpoint with comprehensive checks
- [x] **Status monitoring endpoint** - `/status` with metrics and uptime
- [x] **Graceful shutdown handling** - Signal handlers for clean shutdown
- [ ] No file-based logging (only console)
- [ ] No monitoring/alerting integration
- [ ] No webhook event persistence/replay

## Testing

### Run Test Suite
```bash
cd adws
uv run adw_tests/test_webhook_ngrok.py
```

### Manual Testing
```bash
# Test health endpoint
curl http://localhost:8001/health

# Test webhook with mock payload
curl -X POST http://localhost:8001/gh-webhook \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: issues" \
  -d '{"action":"opened","issue":{"number":999,"body":"Test issue"}}'
```

## Troubleshooting

### Port Already in Use
```bash
lsof -i :8001
kill -9 <PID>
```

### Ngrok Not Starting
1. Check authtoken: `echo $NGROK_AUTHTOKEN`
2. Check ngrok config: `ngrok config check`
3. Kill existing: `killall ngrok`
4. Check logs: `ngrok diagnose`

### Webhook Not Triggering
1. Check GitHub webhook recent deliveries
2. Verify webhook URL is accessible
3. Check server logs for errors
4. Test with curl (see Manual Testing)

### ADW Workflow Not Running
1. Check `agents/` directory for logs
2. Verify Claude Code CLI works: `claude --version`
3. Check environment variables are loaded
4. Test workflow manually: `uv run adw_plan_build.py <issue_number>`

## Best Practices

### For Development
- Use ngrok with `--tunnel` flag
- Monitor logs in real-time
- Test with mock payloads first
- Keep ngrok sessions short (rate limits)

### For Production
- Use webhook secrets (when implemented)
- Set up monitoring and alerting
- Use a queue for webhook processing
- Implement retry logic
- Log to files with rotation
- Use systemd or supervisor for process management

## Key Features

### Automatic Configuration
- **GitHub Webhook Management**: Auto-configures webhooks using gh CLI
- **Port Management**: Handles port conflicts automatically
- **Ngrok Integration**: Seamless tunnel creation with auth token
- **URL Updates**: Automatically updates webhook URL on restart

### Workflow Triggers
Supports multiple ADW workflow triggers via issue/comment keywords:
- `adw_plan` - Planning phase only
- `adw_build <adw_id>` - Build from existing plan
- `adw_test` - Testing phase
- `adw_plan_build` - Combined plan and build
- `adw_plan_build_test` - Full pipeline

### Monitoring & Health
- `/status` - Server metrics, uptime, webhook counts
- `/health` - Comprehensive health check
- Real-time logging to console
- Webhook processing metrics

## Architecture Notes

### Request Flow
1. GitHub sends webhook to public URL
2. Ngrok/tunnel forwards to localhost:8001
3. FastAPI validates and processes request
4. ADW workflow triggered in background
5. Response sent immediately (< 10s)

### State Management
- No persistent state between restarts
- ADW workflows use file-based state in `agents/`
- Each workflow gets unique 8-char ID

### Error Handling
- Currently fails fast (exits on errors)
- Should implement retry logic
- Should queue failed webhooks

## Future Improvements

### High Priority
1. Implement webhook signature validation
2. Add persistent ngrok domain or production deployment
3. Add file-based logging with rotation
4. Implement retry logic for failures

### Medium Priority
1. Add webhook event queueing
2. Implement rate limiting
3. Add monitoring/metrics endpoint
4. Create systemd service file

### Low Priority
1. Web UI for webhook management
2. Webhook replay functionality
3. Multi-repo support
4. Custom workflow routing