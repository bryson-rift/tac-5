# Test Webhook Data

This file contains mock GitHub webhook payload data for testing the ADW webhook integration. Use this data to validate that the webhook system is receiving and processing GitHub events correctly.

## Purpose

This test file provides realistic mock webhook payloads that match the structure of actual GitHub webhook events. The webhook server (`adws/adw_triggers/trigger_webhook.py`) processes these types of events to trigger ADW workflows.

## Workflow Keywords

The ADW system recognizes the following workflow keywords in issue bodies and comments:
- `adw_plan` - Generate plan only
- `adw_build <adw_id>` - Build from existing plan (requires ADW ID)
- `adw_test` - Run tests
- `adw_plan_build` - Plan and build
- `adw_plan_build_test` - Full pipeline (plan, build, and test)

## Mock Webhook Payload Examples

### Example 1: Issue Created Event with `adw_plan_build` keyword

This simulates a new GitHub issue being created with the `adw_plan_build` workflow keyword in the issue body.

```json
{
  "action": "opened",
  "issue": {
    "number": 123,
    "title": "Add user authentication feature",
    "body": "We need to implement user authentication with JWT tokens.\n\nadw_plan_build\n\nAcceptance Criteria:\n- Users can register with email/password\n- Users can login and receive JWT token\n- Protected routes validate JWT tokens",
    "state": "open",
    "user": {
      "login": "developer123",
      "id": 12345678,
      "type": "User"
    },
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T10:30:00Z",
    "labels": [],
    "assignees": [],
    "html_url": "https://github.com/owner/repository/issues/123"
  },
  "repository": {
    "id": 87654321,
    "name": "repository",
    "full_name": "owner/repository",
    "private": false,
    "owner": {
      "login": "owner",
      "id": 11111111
    },
    "html_url": "https://github.com/owner/repository"
  },
  "sender": {
    "login": "developer123",
    "id": 12345678,
    "type": "User"
  }
}
```

**Expected Behavior:**
- Webhook server detects `adw_plan_build` keyword in issue body
- Triggers planning and implementation workflow
- Posts comment to issue with ADW ID
- Creates feature branch and implementation plan
- Implements the solution and creates PR

### Example 2: Issue Comment Event with `adw_test` keyword

This simulates a comment being added to an existing issue with the `adw_test` workflow keyword.

```json
{
  "action": "created",
  "issue": {
    "number": 456,
    "title": "Fix database connection timeout",
    "body": "Users are experiencing database connection timeouts after 30 seconds of inactivity.",
    "state": "open",
    "user": {
      "login": "bugfixer",
      "id": 98765432,
      "type": "User"
    },
    "created_at": "2025-01-14T15:00:00Z",
    "updated_at": "2025-01-15T11:45:00Z",
    "labels": [
      {
        "name": "bug",
        "color": "d73a4a"
      }
    ],
    "assignees": [],
    "html_url": "https://github.com/owner/repository/issues/456"
  },
  "comment": {
    "id": 987654321,
    "user": {
      "login": "tester123",
      "id": 22222222,
      "type": "User"
    },
    "body": "The fix looks good. Let's run the test suite to validate.\n\nadw_test",
    "created_at": "2025-01-15T11:45:00Z",
    "updated_at": "2025-01-15T11:45:00Z",
    "html_url": "https://github.com/owner/repository/issues/456#issuecomment-987654321"
  },
  "repository": {
    "id": 87654321,
    "name": "repository",
    "full_name": "owner/repository",
    "private": false,
    "owner": {
      "login": "owner",
      "id": 11111111
    },
    "html_url": "https://github.com/owner/repository"
  },
  "sender": {
    "login": "tester123",
    "id": 22222222,
    "type": "User"
  }
}
```

**Expected Behavior:**
- Webhook server detects `adw_test` keyword in comment body
- Ignores if comment is from ADW-BOT (prevents loops)
- Triggers test workflow for issue #456
- Runs test suite and reports results
- Posts test results as comment on issue

### Example 3: Issue Comment Event with `adw_build` keyword and ADW ID

This simulates continuing a workflow with a specific ADW ID.

```json
{
  "action": "created",
  "issue": {
    "number": 789,
    "title": "Refactor payment processing module",
    "body": "The payment processing module needs refactoring to improve maintainability.",
    "state": "open",
    "user": {
      "login": "architect",
      "id": 33333333,
      "type": "User"
    },
    "created_at": "2025-01-13T09:00:00Z",
    "updated_at": "2025-01-15T14:20:00Z",
    "labels": [
      {
        "name": "refactor",
        "color": "fbca04"
      }
    ],
    "assignees": [],
    "html_url": "https://github.com/owner/repository/issues/789"
  },
  "comment": {
    "id": 111222333,
    "user": {
      "login": "developer123",
      "id": 12345678,
      "type": "User"
    },
    "body": "Resume the implementation with the existing plan.\n\nadw_build a1b2c3d4",
    "created_at": "2025-01-15T14:20:00Z",
    "updated_at": "2025-01-15T14:20:00Z",
    "html_url": "https://github.com/owner/repository/issues/789#issuecomment-111222333"
  },
  "repository": {
    "id": 87654321,
    "name": "repository",
    "full_name": "owner/repository",
    "private": false,
    "owner": {
      "login": "owner",
      "id": 11111111
    },
    "html_url": "https://github.com/owner/repository"
  },
  "sender": {
    "login": "developer123",
    "id": 12345678,
    "type": "User"
  }
}
```

**Expected Behavior:**
- Webhook server detects `adw_build` keyword with ADW ID `a1b2c3d4`
- Loads existing state for ADW ID `a1b2c3d4`
- Continues implementation using existing plan
- Creates commits and updates PR

### Example 4: Issue Comment from ADW-BOT (should be ignored)

This simulates a comment from the ADW bot itself, which should be ignored to prevent infinite loops.

```json
{
  "action": "created",
  "issue": {
    "number": 123,
    "title": "Add user authentication feature",
    "body": "We need to implement user authentication with JWT tokens.\n\nadw_plan_build",
    "state": "open",
    "user": {
      "login": "developer123",
      "id": 12345678,
      "type": "User"
    },
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T10:35:00Z",
    "html_url": "https://github.com/owner/repository/issues/123"
  },
  "comment": {
    "id": 444555666,
    "user": {
      "login": "github-actions[bot]",
      "id": 41898282,
      "type": "Bot"
    },
    "body": "[ADW-BOT] 🤖 ADW Webhook: Detected `adw_plan_build` workflow request\n\nStarting workflow with ID: `e5f6g7h8`\nReason: New issue with adw_plan_build workflow\n\nLogs will be available at: `agents/e5f6g7h8/adw_plan_build/`",
    "created_at": "2025-01-15T10:35:00Z",
    "updated_at": "2025-01-15T10:35:00Z",
    "html_url": "https://github.com/owner/repository/issues/123#issuecomment-444555666"
  },
  "repository": {
    "id": 87654321,
    "name": "repository",
    "full_name": "owner/repository",
    "private": false,
    "owner": {
      "login": "owner",
      "id": 11111111
    },
    "html_url": "https://github.com/owner/repository"
  },
  "sender": {
    "login": "github-actions[bot]",
    "id": 41898282,
    "type": "Bot"
  }
}
```

**Expected Behavior:**
- Webhook server detects `[ADW-BOT]` identifier in comment
- Ignores comment to prevent infinite loop
- Returns "ignored" status
- No workflow is triggered

## Testing the Webhook

To test the webhook locally:

1. Start the webhook server:
   ```bash
   cd adws/
   uv run adw_triggers/trigger_webhook.py --tunnel
   ```

2. The server will automatically configure the GitHub webhook using the ngrok URL

3. Create a test issue or comment with one of the workflow keywords

4. Monitor the webhook server logs to see event processing

5. Check the `agents/{adw_id}/` directory for workflow execution logs

## Notes

- This is a temporary test file for development and validation
- The mock data structure matches actual GitHub webhook payloads
- All workflow keywords must be lowercase and prefixed with `adw_`
- The webhook server responds within GitHub's 10-second timeout by launching workflows in the background
- The `[ADW-BOT]` identifier prevents webhook processing loops
