# Release Orchestrator

Automates release preparation in GitLab: discovers repositories, collects merged MRs, creates production MRs, and creates release tags.

## How it works

1. A user creates a release issue from the template.
2. A user writes a command in the issue comments.
3. GitLab sends a webhook to the bot (`app.py`).
4. The bot triggers a GitLab pipeline with the requested command.
5. A pipeline job runs one of the scripts:
   - `get_repo.py`
   - `get_mr.py`
   - `mr_prod.py`
   - `create_tag.py`
6. The script updates the release issue and optionally sends a Telegram notification.

## Required variables

### Bot container
- `GITLAB_URL`
- `ORCHESTRATOR_PROJECT_ID`
- `TRIGGER_TOKEN`
- `GROUP_ID`
- `WEBHOOK_SECRET`
- `TRIGGER_REF` (optional, default: `master`)

### Pipeline / scripts
- `GITLAB_URL`
- `GITLAB_TOKEN`
- `GROUP_ID`
- `RELEASE_PROJECT_ID`
- `RELEASE_ISSUE_IID`
- `TELEGRAM_BOT_TOKEN` (optional)
- `TELEGRAM_CHAT_ID` (optional)
- `REPOS_LOOKBACK_DAYS` (optional)
- `REPO_DISCOVERY_WORKERS` (optional)
- `REPO_DISCOVERY_MR_PAGE_SIZE` (optional)
- `CANDIDATES_LOOKBACK_DAYS` (optional)

## Commands

Write one of these commands in a release issue comment:

- `/get_repo` — discover repositories with recent merged MRs in `master`
- `/get_mr` — collect merged MR candidates for selected repositories
- `/mr_prod` — create release branches and production MRs
- `/create_tag` — create release tags for repositories with merged production MRs

## Release issue meta fields

The issue template should contain:

- `Release tag version`
- `Approvers`

Example:

```md
## Meta
- Release tag version: 260325
- Approvers: yerzhan,nikita
