from datetime import datetime
from urllib.parse import quote

import requests

from lib.config import GITLAB_TOKEN, GITLAB_URL


def make_gitlab_session():
    session = requests.Session()
    session.headers.update({"PRIVATE-TOKEN": GITLAB_TOKEN})
    return session


def parse_gitlab_datetime(value):
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def get_issue(session, project_id, issue_iid):
    url = f"{GITLAB_URL}/api/v4/projects/{project_id}/issues/{issue_iid}"
    response = session.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def update_issue(session, project_id, issue_iid, description, verbose=False):
    url = f"{GITLAB_URL}/api/v4/projects/{project_id}/issues/{issue_iid}"
    response = session.put(url, data={"description": description}, timeout=30)
    if verbose:
        print(f"update issue status={response.status_code}")
        print(f"update issue body={response.text}")
    response.raise_for_status()
    return response.json()


def get_project(session, repo_path):
    encoded = quote(repo_path, safe="")
    url = f"{GITLAB_URL}/api/v4/projects/{encoded}"
    response = session.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def list_group_projects(session, group_id):
    projects = []
    page = 1

    while True:
        url = f"{GITLAB_URL}/api/v4/groups/{group_id}/projects"
        response = session.get(
            url,
            params={
                "per_page": 100,
                "page": page,
                "include_subgroups": True,
            },
            timeout=30,
        )
        response.raise_for_status()
        batch = response.json()

        if not batch:
            break

        projects.extend(batch)
        page += 1

    return projects


def list_merge_requests(session, project_id, **params):
    items = []
    page = 1

    while True:
        url = f"{GITLAB_URL}/api/v4/projects/{project_id}/merge_requests"
        request_params = {
            "per_page": 100,
            "page": page,
            **params,
        }
        response = session.get(url, params=request_params, timeout=30)
        response.raise_for_status()
        batch = response.json()

        if not batch:
            break

        items.extend(batch)
        page += 1

    return items


def list_recent_merged_mrs_first_page(session, project_id, page_size):
    url = f"{GITLAB_URL}/api/v4/projects/{project_id}/merge_requests"
    response = session.get(
        url,
        params={
            "state": "merged",
            "target_branch": "master",
            "per_page": page_size,
            "page": 1,
            "order_by": "updated_at",
            "sort": "desc",
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def list_open_merge_requests(session, project_id, source_branch, target_branch):
    url = f"{GITLAB_URL}/api/v4/projects/{project_id}/merge_requests"
    response = session.get(
        url,
        params={
            "state": "opened",
            "source_branch": source_branch,
            "target_branch": target_branch,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def list_merged_merge_requests(session, project_id, source_branch, target_branch):
    url = f"{GITLAB_URL}/api/v4/projects/{project_id}/merge_requests"
    response = session.get(
        url,
        params={
            "state": "merged",
            "source_branch": source_branch,
            "target_branch": target_branch,
            "order_by": "updated_at",
            "sort": "desc",
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def create_branch_if_missing(session, project_id, branch_name, ref="master", verbose=False):
    get_url = f"{GITLAB_URL}/api/v4/projects/{project_id}/repository/branches/{quote(branch_name, safe='')}"
    get_response = session.get(get_url, timeout=30)

    if get_response.status_code == 200:
        return False

    if get_response.status_code != 404:
        get_response.raise_for_status()

    url = f"{GITLAB_URL}/api/v4/projects/{project_id}/repository/branches"
    payload = {
        "branch": branch_name,
        "ref": ref,
    }
    response = session.post(url, json=payload, timeout=30)
    if verbose:
        print(f"create branch status={response.status_code}")
        print(f"create branch body={response.text}")
    response.raise_for_status()
    return True


def get_branch(session, project_id, branch_name):
    encoded_branch = quote(branch_name, safe="")
    url = f"{GITLAB_URL}/api/v4/projects/{project_id}/repository/branches/{encoded_branch}"
    response = session.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def get_tag(session, project_id, tag_name):
    encoded_tag = quote(tag_name, safe="")
    url = f"{GITLAB_URL}/api/v4/projects/{project_id}/repository/tags/{encoded_tag}"
    response = session.get(url, timeout=30)

    if response.status_code == 404:
        return None

    response.raise_for_status()
    return response.json()


def create_tag(session, project_id, tag_name, ref, message, verbose=False):
    existing = get_tag(session, project_id, tag_name)
    if existing:
        return existing, False

    url = f"{GITLAB_URL}/api/v4/projects/{project_id}/repository/tags"
    response = session.post(
        url,
        data={
            "tag_name": tag_name,
            "ref": ref,
            "message": message,
        },
        timeout=30,
    )
    if verbose:
        print(f"create tag status={response.status_code}")
        print(f"create tag body={response.text}")
    response.raise_for_status()
    return response.json(), True


def search_user(session, username):
    url = f"{GITLAB_URL}/api/v4/users"
    response = session.get(url, params={"username": username}, timeout=30)
    response.raise_for_status()
    users = response.json()
    if not users:
        return None
    return users[0]


def resolve_reviewer_ids(session, usernames, verbose=False):
    ids = []
    for username in usernames:
        user = search_user(session, username)
        if verbose:
            print(f"username={username}, user={user}")
        if user:
            ids.append(user["id"])
    return ids


def update_merge_request(session, project_id, merge_request_iid, title, assignee_id, reviewer_ids, verbose=False):
    url = f"{GITLAB_URL}/api/v4/projects/{project_id}/merge_requests/{merge_request_iid}"
    payload = {
        "title": title,
        "assignee_ids": [assignee_id] if assignee_id else [],
        "reviewer_ids": reviewer_ids,
        "remove_source_branch": True,
        "squash": True,
    }

    response = session.put(url, json=payload, timeout=30)
    if verbose:
        print(f"update MR status={response.status_code}")
        print(f"update MR body={response.text}")
    response.raise_for_status()
    return response.json()


def create_merge_request(session, project_id, title, source_branch, target_branch, assignee_id, reviewer_ids, verbose=False):
    existing = list_open_merge_requests(session, project_id, source_branch, target_branch)
    if existing:
        if verbose:
            print(f"existing MR found for {source_branch} -> {target_branch}, updating title/reviewers/assignee")
        return update_merge_request(
            session=session,
            project_id=project_id,
            merge_request_iid=existing[0]["iid"],
            title=title,
            assignee_id=assignee_id,
            reviewer_ids=reviewer_ids,
            verbose=verbose,
        )

    url = f"{GITLAB_URL}/api/v4/projects/{project_id}/merge_requests"
    payload = {
        "title": title,
        "source_branch": source_branch,
        "target_branch": target_branch,
        "assignee_ids": [assignee_id] if assignee_id else [],
        "reviewer_ids": reviewer_ids,
        "remove_source_branch": True,
        "squash": True,
    }

    response = session.post(url, json=payload, timeout=30)
    if verbose:
        print(f"create MR status={response.status_code}")
        print(f"create MR body={response.text}")
    response.raise_for_status()
    return response.json()