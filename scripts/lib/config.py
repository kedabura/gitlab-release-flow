import os

GITLAB_URL = os.environ["GITLAB_URL"].rstrip("/")
GITLAB_TOKEN = os.environ["GITLAB_TOKEN"]
GROUP_ID = os.environ.get("GROUP_ID", "")
RELEASE_PROJECT_ID = os.environ["RELEASE_PROJECT_ID"]
RELEASE_ISSUE_IID = os.environ["RELEASE_ISSUE_IID"]

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

DEFAULT_MR_REVIEWERS = [x.strip() for x in os.getenv("MR_REVIEWERS", "").split(",") if x.strip()]