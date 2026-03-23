import os
from datetime import datetime, timedelta, UTC
from concurrent.futures import ThreadPoolExecutor, as_completed

from lib.config import GROUP_ID, RELEASE_ISSUE_IID, RELEASE_PROJECT_ID
from lib.gitlab_api import (
    get_issue,
    list_group_projects,
    list_recent_merged_mrs_first_page,
    make_gitlab_session,
    parse_gitlab_datetime,
    update_issue,
)
from lib.issue_blocks import replace_block
from lib.issue_parser import extract_meta_value

repos_lookback_days = int(os.getenv("REPOS_LOOKBACK_DAYS", "7"))
repo_discovery_workers = int(os.getenv("REPO_DISCOVERY_WORKERS", "8"))
mr_page_size = int(os.getenv("REPO_DISCOVERY_MR_PAGE_SIZE", "20"))

session = make_gitlab_session()


def classify_repo(repo_name):
    name = repo_name.lower()
    if "ios" in name or "android" in name or "mobile" in name:
        return "Mobile"
    if "web" in name or "front" in name or "frontend" in name or "ui" in name:
        return "Frontend"
    if "api" in name or "back" in name or "backend" in name or "monolith" in name:
        return "Backend"
    return "Other"


def project_has_recent_merged_mr(project, threshold):
    local_session = make_gitlab_session()
    try:
        merge_requests = list_recent_merged_mrs_first_page(local_session, project["id"], mr_page_size)
        for mr in merge_requests:
            merged_at = parse_gitlab_datetime(mr.get("merged_at"))
            if merged_at and merged_at >= threshold:
                return project
        return None
    except Exception as e:
        print(f"skip project {project.get('path_with_namespace')}: {e}")
        return None
    finally:
        local_session.close()


issue = get_issue(session, RELEASE_PROJECT_ID, RELEASE_ISSUE_IID)
description = issue.get("description") or ""

release_tag_version = extract_meta_value(description, "Release tag version", "260323")

now_utc = datetime.now(UTC)
lookback_from = now_utc - timedelta(days=repos_lookback_days)

projects = list_group_projects(session, GROUP_ID)
projects = [
    project for project in projects
    if not project.get("archived")
    and project["path_with_namespace"].split("/")[-1] != "release-automation"
]

filtered_projects = []

with ThreadPoolExecutor(max_workers=repo_discovery_workers) as executor:
    futures = [executor.submit(project_has_recent_merged_mr, project, lookback_from) for project in projects]
    for future in as_completed(futures):
        result = future.result()
        if result:
            filtered_projects.append(result)

filtered_projects.sort(key=lambda project: project["path_with_namespace"])

groups = {
    "Backend": [],
    "Frontend": [],
    "Mobile": [],
    "Other": [],
}

for project in filtered_projects:
    repo_name = project["path_with_namespace"]
    groups[classify_repo(repo_name)].append(repo_name)

parts = []
for section in ["Backend", "Frontend", "Mobile", "Other"]:
    repos = groups[section]
    if not repos:
        continue

    parts.append(f"### {section}")
    for repo in repos:
        parts.append(f"- [ ] {repo}")
        parts.append(f"  - release_tag: {release_tag_version}")
        parts.append("")

new_block = "\n".join(parts).strip() if parts else "- [ ] no repositories found with merged MR in master for the selected lookback period"

updated = replace_block(
    description,
    "<!-- automation:repos:start -->",
    "<!-- automation:repos:end -->",
    new_block,
)

updated = replace_block(
    updated,
    "<!-- automation:tasks:start -->",
    "<!-- automation:tasks:end -->",
    "- loading...",
)

updated = replace_block(
    updated,
    "<!-- automation:prepare:start -->",
    "<!-- automation:prepare:end -->",
    "- pending",
)

updated = replace_block(
    updated,
    "<!-- automation:tags:start -->",
    "<!-- automation:tags:end -->",
    "- pending",
)

update_issue(session, RELEASE_PROJECT_ID, RELEASE_ISSUE_IID, updated)
print("repositories block updated, tasks block reset, preparation block reset, tags block reset")