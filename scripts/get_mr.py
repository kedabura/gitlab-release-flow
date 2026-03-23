import os
from datetime import datetime, timedelta, UTC

from lib.config import RELEASE_ISSUE_IID, RELEASE_PROJECT_ID
from lib.gitlab_api import get_issue, get_project, list_merge_requests, make_gitlab_session, parse_gitlab_datetime, update_issue
from lib.issue_blocks import replace_block
from lib.issue_parser import extract_selected_repos, find_issue_key

candidates_lookback_days = int(os.getenv("CANDIDATES_LOOKBACK_DAYS", "7"))

session = make_gitlab_session()

now_utc = datetime.now(UTC)
lookback_from = now_utc - timedelta(days=candidates_lookback_days)

issue = get_issue(session, RELEASE_PROJECT_ID, RELEASE_ISSUE_IID)
description = issue.get("description") or ""
selected_repos = extract_selected_repos(description)

print(f"selected_repos={selected_repos}")

parts = []

for repo in selected_repos:
    project = get_project(session, repo)
    merge_requests = list_merge_requests(
        session,
        project["id"],
        state="merged",
        target_branch="master",
        order_by="updated_at",
        sort="desc",
    )
    recent_mrs = []

    for mr in merge_requests:
        merged_at_raw = mr.get("merged_at")
        merged_at = parse_gitlab_datetime(merged_at_raw)

        if not merged_at:
            continue

        if merged_at < lookback_from:
            continue

        recent_mrs.append(mr)

    print(f"repo={repo}, project_id={project['id']}, recent_mr_count={len(recent_mrs)}")

    if not recent_mrs:
        continue

    parts.append(f"### {repo}")

    seen = set()

    for mr in recent_mrs:
        issue_key = find_issue_key(mr.get("title", "")) or find_issue_key(mr.get("description", ""))
        title = (mr.get("title") or "").strip()
        mr_ref = f'!{mr["iid"]}'
        web_url = f'{mr.get("web_url", "")}+'
        merged_at = mr.get("merged_at", "")
        task_title = issue_key or title

        unique_key = f"{task_title}:{mr_ref}"
        if unique_key in seen:
            continue
        seen.add(unique_key)

        parts.append(f"- task: {task_title}")
        parts.append(f"  - mr: {mr_ref} ({web_url})")
        parts.append(f"  - merged_at: {merged_at}")
        parts.append(f"  - summary: {title}")
        parts.append("")

new_block = "\n".join(parts).strip() if parts else f"- no candidates found for selected repositories in the last {candidates_lookback_days} days"

updated = replace_block(
    description,
    "<!-- automation:tasks:start -->",
    "<!-- automation:tasks:end -->",
    new_block,
)

update_issue(session, RELEASE_PROJECT_ID, RELEASE_ISSUE_IID, updated)
print("tasks block updated")