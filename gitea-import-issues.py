import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

GITEA_URL = os.getenv("GITEA_URL")
OWNER = os.getenv("OWNER")
REPO = os.getenv("REPO")
TOKEN = os.getenv("TOKEN")

def get_existing_labels():
    url = f"{GITEA_URL}/api/v1/repos/{OWNER}/{REPO}/labels"
    headers = {"Authorization": f"token {TOKEN}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return {label['name']: label['id'] for label in response.json()}
    else:
        print(f"Failed to retrieve labels: {response.status_code} {response.text}")
        return {}

def create_label(name, color="#ffffff", description=""):
    url = f"{GITEA_URL}/api/v1/repos/{OWNER}/{REPO}/labels"
    headers = {"Authorization": f"token {TOKEN}"}
    payload = {
        "name": name,
        "color": color.lstrip("#"),
        "description": description
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 201:
        label = response.json()
        print(f"Label '{name}' created.")
        return label['id']
    elif response.status_code == 409:
        print(f"Label '{name}' already exists.")
        return None
    else:
        print(f"Failed to create label '{name}': {response.status_code} {response.text}")
        return None

def get_existing_milestones():
    url = f"{GITEA_URL}/api/v1/repos/{OWNER}/{REPO}/milestones"
    headers = {"Authorization": f"token {TOKEN}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return {ms['title']: ms['id'] for ms in response.json()}
    else:
        print(f"Failed to retrieve milestones: {response.status_code} {response.text}")
        return {}

def create_milestone(title, description=""):
    url = f"{GITEA_URL}/api/v1/repos/{OWNER}/{REPO}/milestones"
    headers = {"Authorization": f"token {TOKEN}"}
    payload = {
        "title": title,
        "description": description
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 201:
        milestone = response.json()
        print(f"Milestone '{title}' created.")
        return milestone['id']
    elif response.status_code == 409:
        print(f"Milestone '{title}' already exists.")
        return None
    else:
        print(f"Failed to create milestone '{title}': {response.status_code} {response.text}")
        return None

def create_issue(title, body, label_ids=None, milestone_id=None):
    url = f"{GITEA_URL}/api/v1/repos/{OWNER}/{REPO}/issues"
    headers = {"Authorization": f"token {TOKEN}"}
    payload = {
        "title": title,
        "body": body
    }
    if label_ids:
        payload["labels"] = label_ids
    if milestone_id:
        payload["milestone"] = milestone_id
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 201:
        issue = response.json()
        print(f"Issue '{title}' created with number {issue['number']}.")
        return issue['number']
    else:
        print(f"Failed to create issue '{title}': {response.status_code} {response.text}")
        return None

def import_issue(issue_data, existing_labels, existing_milestones):
    # Process labels
    label_ids = []
    for label in issue_data.get("labels", []):
        label_name = label.get("name")
        if label_name in existing_labels:
            label_ids.append(existing_labels[label_name])
        else:
            label_id = create_label(label_name)
            if label_id:
                existing_labels[label_name] = label_id
                label_ids.append(label_id)

    # Process milestone
    milestone_id = None
    milestone = issue_data.get("milestone")
    if milestone:
        milestone_title = milestone.get("title")
        if milestone_title in existing_milestones:
            milestone_id = existing_milestones[milestone_title]
        else:
            milestone_id = create_milestone(milestone_title)
            if milestone_id:
                existing_milestones[milestone_title] = milestone_id

    # Create issue
    title = issue_data.get("title")
    body = issue_data.get("body", "")
    create_issue(title, body, label_ids, milestone_id)

def import_issues_from_file(json_file_path):
    with open(json_file_path, 'r', encoding='utf-8') as f:
        issues = json.load(f)

    existing_labels = get_existing_labels()
    existing_milestones = get_existing_milestones()

    for issue_data in issues:
        import_issue(issue_data, existing_labels, existing_milestones)

# Example usage:
if __name__ == "__main__":
    import_issues_from_file('gitea.icosahedron.sreadsheet-api.sorted.issues.json')
