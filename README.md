# Release Orchestrator

Automates release preparation in GitLab: selects repositories, collects merged MRs, creates production MRs, and creates release tags.

## How it works

The service listens for GitLab issue comment webhooks and triggers GitLab pipelines based on commands posted in a release issue.

Flow:

1. Create a release issue from template
2. Comment with a command
3. Webhook triggers pipeline
4. Pipeline runs one of the scripts
5. Issue is updated with results

## Supported commands

- `/get_repo` — discover repositories with recent merged MRs in `master`
- `/get_mr` — collect merged MR candidates for selected repositories
- `/mr_prod` — create release branches and production merge requests
- `/create_tag` — create release tags after release MRs are merged into `production`

## Project structure

```text
release-orchestrator/
├── release-bot/
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
├── scripts/
│   ├── create_tag.py
│   ├── get_mr.py
│   ├── get_repo.py
│   ├── mr_prod.py
│   └── lib/
│       ├── config.py
│       ├── gitlab_api.py
│       ├── issue_blocks.py
│       ├── issue_parser.py
│       └── telegram_api.py
└── .gitlab-ci.yml