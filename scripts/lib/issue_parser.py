import re

from lib.issue_blocks import extract_block


def extract_meta_value(description, field_name, default_value=""):
    pattern = rf"^- {re.escape(field_name)}:\s*(.+)$"
    match = re.search(pattern, description or "", re.MULTILINE)
    if match:
        return match.group(1).strip()
    return default_value


def parse_csv_list(value):
    return [x.strip() for x in (value or "").split(",") if x.strip()]


def extract_selected_repos(description):
    block = extract_block(description, "<!-- automation:repos:start -->", "<!-- automation:repos:end -->")
    if block is None:
        return []

    repos = []

    for line in block.splitlines():
        repo_match = re.match(r"^\s*-\s+\[x\]\s+(.+?)\s*$", line.strip(), re.IGNORECASE)
        if repo_match:
            repos.append(repo_match.group(1).strip())

    return repos


def extract_selected_repos_with_tags(description, fallback_release_tag):
    block = extract_block(description, "<!-- automation:repos:start -->", "<!-- automation:repos:end -->")
    if block is None:
        return []

    lines = block.splitlines()
    repos = []
    current_repo = None

    for raw_line in lines:
        line = raw_line.rstrip()

        repo_match = re.match(r"^\s*-\s+\[(x| )\]\s+(.+?)\s*$", line, re.IGNORECASE)
        if repo_match:
            if current_repo and current_repo["selected"]:
                repos.append({
                    "repo": current_repo["repo"],
                    "release_tag": current_repo["release_tag"],
                })

            selected_flag = repo_match.group(1).lower() == "x"
            repo_name = repo_match.group(2).strip()

            current_repo = {
                "selected": selected_flag,
                "repo": repo_name,
                "release_tag": fallback_release_tag,
            }
            continue

        section_match = re.match(r"^\s*###\s+.+$", line)
        if section_match:
            if current_repo and current_repo["selected"]:
                repos.append({
                    "repo": current_repo["repo"],
                    "release_tag": current_repo["release_tag"],
                })
            current_repo = None
            continue

        if current_repo:
            tag_match = re.match(r"^\s*-\s+release_tag:\s*(.+?)\s*$", line, re.IGNORECASE)
            if tag_match:
                current_repo["release_tag"] = tag_match.group(1).strip()

    if current_repo and current_repo["selected"]:
        repos.append({
            "repo": current_repo["repo"],
            "release_tag": current_repo["release_tag"],
        })

    return repos


def find_issue_key(text):
    if not text:
        return None

    patterns = [
        r"\b([A-Z][A-Z0-9]+-\d+)\b",
        r"\b([A-Za-zА-Яа-я]+-\d+)\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)

    return None