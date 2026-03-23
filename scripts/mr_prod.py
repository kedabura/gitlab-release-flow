from lib.config import DEFAULT_MR_REVIEWERS, RELEASE_ISSUE_IID, RELEASE_PROJECT_ID
from lib.gitlab_api import (
    create_branch_if_missing,
    create_merge_request,
    get_issue,
    get_project,
    make_gitlab_session,
    resolve_reviewer_ids,
    update_issue,
)
from lib.issue_blocks import replace_block
from lib.issue_parser import extract_meta_value, extract_selected_repos_with_tags, parse_csv_list
from lib.telegram_api import send_telegram_message

session = make_gitlab_session()

issue = get_issue(session, RELEASE_PROJECT_ID, RELEASE_ISSUE_IID)
description = issue.get("description") or ""
issue_title = issue.get("title") or f"release issue {RELEASE_ISSUE_IID}"
issue_author_id = issue.get("author", {}).get("id") or issue.get("author_id")

fallback_release_tag = extract_meta_value(description, "Release tag version", "260323")
approvers_raw = extract_meta_value(description, "Approvers", "")
approvers = parse_csv_list(approvers_raw) if approvers_raw else DEFAULT_MR_REVIEWERS

selected_repos = extract_selected_repos_with_tags(description, fallback_release_tag)
reviewer_ids = resolve_reviewer_ids(session, approvers, verbose=True)

print(f"default MR_REVIEWERS={DEFAULT_MR_REVIEWERS}")
print(f"issue approvers raw={approvers_raw}")
print(f"effective approvers={approvers}")
print(f"resolved reviewer_ids={reviewer_ids}")
print(f"selected_repos={selected_repos}")

results = []
mr_links = []

for item in selected_repos:
    repo = item["repo"]
    release_tag = item["release_tag"]
    branch_name = f"master_{release_tag}"

    project = get_project(session, repo)
    project_id = project["id"]

    create_branch_if_missing(
        session=session,
        project_id=project_id,
        branch_name=branch_name,
        ref="master",
        verbose=True,
    )

    mr = create_merge_request(
        session=session,
        project_id=project_id,
        title=f"release_{release_tag}",
        source_branch=branch_name,
        target_branch="production",
        assignee_id=issue_author_id,
        reviewer_ids=reviewer_ids,
        verbose=True,
    )

    print(f"MR reviewers returned={mr.get('reviewers')}")
    print(f"MR assignees returned={mr.get('assignees')}")

    results.append(f"### {repo}")
    results.append(f"- branch: {branch_name}")
    results.append(f"- mr: !{mr['iid']} ({mr['web_url']})")
    results.append("")

    mr_links.append({
        "repo": repo,
        "url": mr["web_url"],
        "iid": mr["iid"],
    })

new_status = "\n".join(results).strip() if results else "- no selected repositories"

updated = replace_block(
    description,
    "<!-- automation:prepare:start -->",
    "<!-- automation:prepare:end -->",
    new_status,
)

update_issue(session, RELEASE_PROJECT_ID, RELEASE_ISSUE_IID, updated, verbose=True)

if mr_links:
    lines = []
    lines.append(f"Нужно проставить approve по релизу: {issue_title}")
    lines.append("")
    for item in mr_links:
        lines.append(f"{item['repo']} - {item['url']}")
    telegram_text = "\n".join(lines)
    send_telegram_message(telegram_text, verbose=True)

print("release branches and merge requests created")