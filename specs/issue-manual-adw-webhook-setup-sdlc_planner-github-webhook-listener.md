# Chore: Setup GitHub Webhook Listener for tac-5 Repository

## Chore Description
Set up the GitHub webhook listener for the tac-5 repository to enable automatic triggering of ADW workflows when new GitHub issues are created. The webhook listener was successfully configured in tac-4 for manual execution but the webhook method was never tested. We need to properly configure tac-5 to work with GitHub webhooks, including creating a new GitHub repository if needed and ensuring all environment variables and configurations are properly set.

## Relevant Files
Use these files to resolve the chore:

- `.env` - Environment configuration file that needs proper GitHub repository URL settings
- `.env.sample` - Template showing required environment variables
- `adws/adw_triggers/trigger_webhook.py` - Webhook listener script that receives GitHub events
- `adws/adw_modules/github.py` - Contains `get_repo_url()` function that reads git remote origin
- `adws/README.md` - Documentation for ADW system setup and configuration
- `.git/config` - Git configuration that needs remote origin setup

### New Files
None required - all necessary files exist but need proper configuration

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Create GitHub Repository for tac-5
- Create a new GitHub repository named `tac-5` under the `bryson-rift` account
- Use `gh repo create bryson-rift/tac-5 --public --description "TAC-5 Learning Test Repository"`
- This will provide the GitHub repository needed for webhook integration

### 2. Configure Git Remote Origin
- Add the newly created GitHub repository as the remote origin
- Use `git remote add origin https://github.com/bryson-rift/tac-5.git`
- This allows the ADW system to automatically detect the repository URL via `git remote get-url origin`

### 3. Verify Environment Variables
- Confirm `.env` file contains all required environment variables:
  - `GITHUB_PAT` - Already present and configured
  - `ANTHROPIC_API_KEY` - Already present and configured
  - `CLAUDE_CODE_PATH` - Already present and configured
- Note: `GITHUB_REPO_URL` is NOT needed as the system auto-detects it from git remote

### 4. Push Initial Code to GitHub
- Stage all current work: `git add .`
- Create initial commit: `git commit -m "Initial tac-5 repository setup"`
- Push to GitHub: `git push -u origin main`
- This establishes the connection between local and remote repositories

### 5. Configure GitHub Webhook (Manual Setup Required)
- Navigate to the GitHub repository settings: `https://github.com/bryson-rift/tac-5/settings/webhooks`
- Add a new webhook with:
  - Payload URL: `<your-webhook-endpoint>/gh-webhook` (requires public endpoint via ngrok/cloudflare tunnel)
  - Content type: `application/json`
  - Events: Select "Issues" and "Issue comments"
  - Active: Checked
- Note: The webhook endpoint must be publicly accessible (use ngrok, cloudflare tunnel, or cloud hosting)

### 6. Test Webhook Listener Locally
- Start the webhook listener: `cd adws && uv run adw_triggers/trigger_webhook.py`
- Verify it starts on port 8001 (default)
- Check health endpoint: `curl http://localhost:8001/health`
- Monitor console output for incoming webhook events

### 7. Expose Webhook Endpoint (If Testing Locally)
- Option A: Use ngrok: `ngrok http 8001`
- Option B: Use cloudflare tunnel with `CLOUDFLARED_TUNNEL_TOKEN` in `.env`
- Update GitHub webhook with the public URL provided by the tunnel service
- This allows GitHub to send events to your local webhook listener

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `git remote get-url origin` - Should return `https://github.com/bryson-rift/tac-5.git`
- `gh repo view bryson-rift/tac-5 --json url` - Should show the repository exists
- `cd adws && uv run adw_tests/health_check.py` - Run ADW health check to ensure all dependencies are met
- `cd adws && uv run adw_triggers/trigger_webhook.py` - Start webhook listener without errors
- `curl http://localhost:8001/health` - Health endpoint should return healthy status

## Notes
- The main difference between tac-4 and tac-5 setup is that tac-5 doesn't have a GitHub remote configured yet
- The ADW system automatically detects the repository from `git remote get-url origin`, so no `GITHUB_REPO_URL` environment variable is needed
- For production webhook usage, consider using a cloud-hosted solution instead of local tunneling
- The webhook listener filters out bot comments (containing `[ADW-BOT]`) to prevent infinite loops
- Webhook events trigger ADW workflows in background processes to meet GitHub's 10-second timeout requirement