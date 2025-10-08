# Chore: Review and Document GitHub Webhook and Ngrok Integration

## Chore Description
Review and validate the recently created GitHub webhook and ngrok connection system that automatically updates the webhook URL for each run of `uv run trigger_webhook --tunnel`. Ensure the concept is logically sound, working correctly, and properly documented. Update the README.md to reflect the exact usage instructions and provide clear guidance on how users should run the webhook server and create GitHub issues to trigger ADW workflows (adw_plan, adw_build, adw_test, adw_plan_build, adw_plan_build_test).

## Relevant Files
Use these files to resolve the chore:

- `adws/adw_triggers/trigger_webhook.py` - Main webhook server implementation with ngrok tunnel support and GitHub auto-configuration
- `adws/adw_modules/webhook_manager.py` - GitHub webhook management module for auto-configuration via gh CLI
- `adws/adw_tests/test_webhook_ngrok.py` - Comprehensive test suite for webhook and ngrok integration
- `adws/WEBHOOK_DEPLOYMENT.md` - Existing deployment documentation (needs review and updates)
- `adws/README.md` - ADW system documentation (needs webhook section update)
- `README.md` - Main project README (needs clear webhook usage instructions)
- `adws/adw_modules/webhook_security.py` - Security module for webhook signature validation (if exists, otherwise needs creation)

## Step by Step Tasks

### Review and Test Current Implementation

- Read and analyze the trigger_webhook.py implementation to understand the full workflow
- Review the webhook_manager.py module to understand GitHub API integration via gh CLI
- Test the ngrok tunnel creation with `uv run adws/adw_triggers/trigger_webhook.py --tunnel`
- Verify the webhook auto-configuration works by checking GitHub webhook settings
- Run the test suite with `uv run adws/adw_tests/test_webhook_ngrok.py`
- Document any issues or improvements needed

### Validate Webhook Security

- Check if webhook signature validation is implemented (currently missing per WEBHOOK_DEPLOYMENT.md)
- Review for any security vulnerabilities in the webhook endpoint
- Verify that ADW-BOT comments are properly ignored to prevent infinite loops
- Ensure proper error handling and graceful shutdown mechanisms
- Check rate limiting and request size limit implementations

### Test ADW Workflow Triggers

- Create a test GitHub issue with body containing "adw_plan" and verify it triggers the workflow
- Test issue comment with "adw_build <existing_adw_id>" to verify build workflow
- Test "adw_test" workflow trigger
- Test "adw_plan_build" combined workflow
- Test "adw_plan_build_test" full pipeline workflow
- Verify each workflow creates appropriate comments and logs

### Update Documentation

- Update README.md with a new "GitHub Webhook Integration" section explaining:
  - Prerequisites (ngrok installation, NGROK_AUTHTOKEN setup)
  - How to start the webhook server with tunnel
  - How the auto-configuration works
  - Example GitHub issue formats for each workflow
- Update adws/README.md webhook section with:
  - Detailed explanation of the auto-configuration mechanism
  - Troubleshooting steps for common issues
  - Security best practices
- Review and update WEBHOOK_DEPLOYMENT.md to reflect current implementation

### Create User Guide Examples

- Create example GitHub issues showing proper format for each workflow:
  - Feature request with adw_plan_build
  - Bug report with adw_plan_build_test
  - Chore with adw_plan
  - Build continuation with adw_build and ADW ID
- Document the expected bot responses and workflow progression
- Include troubleshooting steps for common scenarios

### Verify End-to-End Functionality

- Start fresh with no existing webhooks (cleanup if needed)
- Run `uv run adws/adw_triggers/trigger_webhook.py --tunnel`
- Verify webhook is auto-configured in GitHub
- Create a GitHub issue at https://github.com/bryson-rift/tac-5/issues with:
  ```
  Title: Test ADW Integration
  Body:
  /feature Add a test feature
  adw_plan_build
  ```
- Monitor the webhook server logs
- Verify ADW workflow triggers and creates appropriate PR
- Test server restart and webhook URL update

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run adws/adw_tests/test_webhook_ngrok.py` - Run complete test suite for webhook integration
- `uv run adws/adw_modules/webhook_manager.py list` - List all configured webhooks
- `uv run adws/adw_triggers/trigger_webhook.py --tunnel` - Start webhook server with tunnel and verify auto-configuration
- `curl http://localhost:8001/health` - Check webhook server health endpoint
- `curl http://localhost:8001/status` - Check webhook server status and metrics
- `cd app/server && uv run pytest` - Ensure no regressions in main application tests

## Notes
- The webhook system uses gh CLI for GitHub API operations, maintaining consistency with the rest of the ADW system
- Ngrok tunnel URLs change on each restart unless a reserved domain is configured
- The webhook manager automatically updates existing webhooks when the URL changes
- Security improvements are still needed (webhook signature validation not yet implemented)
- Consider implementing a queue system for webhook events to handle high volume scenarios
- The system currently responds immediately to GitHub's 10-second timeout by launching workflows in background