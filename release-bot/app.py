import os
import requests
from fastapi import FastAPI, Header, HTTPException, Request

app = FastAPI()

GITLAB_URL = os.environ["GITLAB_URL"].rstrip("/")
ORCHESTRATOR_PROJECT_ID = os.environ["ORCHESTRATOR_PROJECT_ID"]
TRIGGER_TOKEN = os.environ["TRIGGER_TOKEN"]
GROUP_ID = os.environ["GROUP_ID"]
WEBHOOK_SECRET = os.environ["WEBHOOK_SECRET"]
TRIGGER_REF = os.getenv("TRIGGER_REF", "master")

COMMANDS = {
    "/get_repo": "get_repo",
    "/get_mr": "get_mr",
    "/mr_prod": "mr_prod",
    "/create_tag": "create_tag"
}

def parse_command(note: str):
    first_line = (note or "").strip().splitlines()
    if not first_line:
        return None
    return COMMANDS.get(first_line[0].strip())

def trigger_pipeline(command: str, release_project_id: int, release_issue_iid: int):
    url = f"{GITLAB_URL}/api/v4/projects/{ORCHESTRATOR_PROJECT_ID}/trigger/pipeline"
    data = {
        "token": TRIGGER_TOKEN,
        "ref": TRIGGER_REF,
        "variables[COMMAND]": command,
        "variables[GROUP_ID]": str(GROUP_ID),
        "variables[RELEASE_PROJECT_ID]": str(release_project_id),
        "variables[RELEASE_ISSUE_IID]": str(release_issue_iid),
    }
    response = requests.post(url, data=data, timeout=30)
    response.raise_for_status()
    return response.json()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/gitlab/webhook")
async def gitlab_webhook(
    request: Request,
    x_gitlab_token: str | None = Header(default=None),
    x_gitlab_event: str | None = Header(default=None),
):
    if x_gitlab_token != WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="invalid webhook token")

    payload = await request.json()

    if x_gitlab_event != "Note Hook":
        return {"status": "ignored", "reason": "not note hook"}

    object_attributes = payload.get("object_attributes") or {}
    project = payload.get("project") or {}
    issue = payload.get("issue") or {}

    noteable_type = object_attributes.get("noteable_type")
    note = object_attributes.get("note") or ""

    if noteable_type != "Issue":
        return {"status": "ignored", "reason": "not issue comment"}

    command = parse_command(note)
    if not command:
        return {"status": "ignored", "reason": "unknown command"}

    if not project.get("id") or not issue.get("iid"):
        raise HTTPException(status_code=400, detail="missing project.id or issue.iid")

    pipeline = trigger_pipeline(
        command=command,
        release_project_id=project["id"],
        release_issue_iid=issue["iid"],
    )

    return {
        "status": "ok",
        "command": command,
        "release_project_id": project["id"],
        "release_issue_iid": issue["iid"],
        "pipeline_id": pipeline.get("id"),
        "pipeline_web_url": pipeline.get("web_url"),
    }