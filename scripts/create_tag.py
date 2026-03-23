from lib.config import RELEASE_ISSUE_IID, RELEASE_PROJECT_ID
from lib.gitlab_api import (
    create_tag,
    get_branch,
    get_issue,
    get_project,
    list_merged_merge_requests,
    make_gitlab_session,
    update_issue,
)
from lib.issue_blocks import replace_block
from lib.issue_parser import extract_meta_value, extract_selected_repos_with_tags
from lib.telegram_api import send_telegram_message

session = make_gitlab_session()

issue = get_issue(session, RELEASE_PROJECT_ID, RELEASE_ISSUE_IID)
description = issue.get("description") or ""
issue_title = issue.get("title") or f"release issue {RELEASE_ISSUE_IID}"

fallback_release_tag = extract_meta_value(description, "Release tag version", "260323")
selected_repos = extract_selected_repos_with_tags(description, fallback_release_tag)

print(f"selected_repos={selected_repos}")

results = []
tag_links = []

for item in selected_repos:
    repo = item["repo"]
    release_tag = item["release_tag"]
    branch_name = f"master_{release_tag}"
    tag_name = f"release_{release_tag}"

    project = get_project(session, repo)
    project_id = project["id"]

    merged_mrs = list_merged_merge_requests(
        session,
        project_id=project_id,
        source_branch=branch_name,
        target_branch="production",
    )

    if not merged_mrs:
        results.append(f"### {repo}")
        results.append(f"- tag: {tag_name}")
        results.append(f"- status: skipped")
        results.append(f"- reason: merged MR {branch_name} -> production not found")
        results.append("")
        continue

    mr = merged_mrs[0]

    tag_ref = mr.get("merge_commit_sha") or mr.get("squash_commit_sha")
    if not tag_ref:
        production_branch = get_branch(session, project_id, "production")
        tag_ref = production_branch["commit"]["id"]

    tag_message = f"{issue_title} / {tag_name}"
    tag, created = create_tag(
        session,
        project_id=project_id,
        tag_name=tag_name,
        ref=tag_ref,
        message=tag_message,
        verbose=True,
    )

    from lib.config import GITLAB_URL

    tag_url = f"{GITLAB_URL}/{repo}/-/tags/{tag_name}"

    results.append(f"### {repo}")
    results.append(f"- tag: {tag_name}")
    results.append(f"- ref: {tag_ref}")
    results.append(f"- status: {'created' if created else 'already exists'}")
    results.append(f"- url: {tag_url}")
    results.append("")

    tag_links.append({
        "repo": repo,
        "tag": tag_name,
        "url": tag_url,
    })

new_status = "\n".join(results).strip() if results else "- no selected repositories"

updated = replace_block(
    description,
    "<!-- automation:tags:start -->",
    "<!-- automation:tags:end -->",
    new_status,
)

update_issue(session, RELEASE_PROJECT_ID, RELEASE_ISSUE_IID, updated, verbose=True)

if tag_links:
    lines = []
    lines.append("Релизные теги")
    lines.append("")
    for item in tag_links:
        lines.append(f"{item['repo']} - {item['url']}")
    telegram_text = "\n".join(lines)
    send_telegram_message(telegram_text, verbose=True)

print("release tags processed")