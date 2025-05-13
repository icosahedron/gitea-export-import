import os
import json
import requests
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

GITEA_URL = os.getenv("GITEA_URL")
OWNER = os.getenv("OWNER")
REPO = os.getenv("REPO")
TOKEN = os.getenv("TOKEN")

HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/json"
}

def get_paginated_data(url, params=None):
    if params is None:
        params = {}
    params['limit'] = 100  # Adjust as needed
    page = 1
    results = []
    while True:
        params['page'] = page
        response = requests.get(url, headers=HEADERS, params={'page': params['page'], 'limit': params['limit']})
        response.raise_for_status()
        data = response.json()
        if not data:
            break
        results.extend(data)
        page += 1
    return results

def get_comments(issue_number):
    url = f"{GITEA_URL}/api/v1/repos/{OWNER}/{REPO}/issues/{issue_number}/comments"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    comments = response.json()
    return comments

def get_comment_reactions(comment_number):
    url = f"{GITEA_URL}/api/v1/repos/{OWNER}/{REPO}/issues/comments/{comment_number}/reactions"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    reactions = response.json()
    return reactions

def get_issue_reactions(issue_number):
    url = f"{GITEA_URL}/api/v1/repos/{OWNER}/{REPO}/issues/{issue_number}/reactions"
    try:
        return get_paginated_data(url)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return []
        else:
            raise

def get_issue_dependencies(issue_number):
    """Get dependencies for an issue using the REST API"""
    url = f"{GITEA_URL}/api/v1/repos/{OWNER}/{REPO}/issues/{issue_number}/dependencies"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return []
        else:
            print(f"Error getting issue dependencies: {e}")
            return []

def get_issue_attachments(issue_number):
    """Get attachments for an issue using the REST API"""
    url = f"{GITEA_URL}/api/v1/repos/{OWNER}/{REPO}/issues/{issue_number}/assets"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return []
        else:
            print(f"Error getting issue attachments: {e}")
            return []

def get_comment_attachments(comment_id):
    """Get attachments for a comment using the REST API"""
    url = f"{GITEA_URL}/api/v1/repos/{OWNER}/{REPO}/issues/comments/{comment_id}/assets"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return []
        else:
            print(f"Error getting comment attachments: {e}")
            return []

def download_issue_attachment(issue_number, attachment_id, output_dir):
    """Download an issue attachment using the REST API"""
    url = f"{GITEA_URL}/api/v1/repos/{OWNER}/{REPO}/issues/{issue_number}/assets/{attachment_id}"
    return download_attachment(url, output_dir)

def download_comment_attachment(comment_id, attachment_id, output_dir):
    """Download a comment attachment using the REST API"""
    url = f"{GITEA_URL}/api/v1/repos/{OWNER}/{REPO}/issues/comments/{comment_id}/assets/{attachment_id}"
    return download_attachment(url, output_dir)

def download_attachment(url, output_dir):
    """Download an attachment and save it to the output directory"""
    try:
        # First get the attachment metadata
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()

        # Extract attachment info from response
        attachment_info = response.json()

        # Create directory for storing attachments
        attachment_dir = Path(output_dir)
        attachment_dir.mkdir(parents=True, exist_ok=True)

        # Get the download URL and append /raw to it for actual file content
        download_url = attachment_info.get('browser_download_url')
        if not download_url:
            # Try to construct download URL if not provided
            download_url = f"{url}/raw"
            print(f"Using constructed download URL: {download_url}")

        # Download the actual file content
        file_response = requests.get(download_url, headers=HEADERS)
        file_response.raise_for_status()

        # Get filename from attachment info
        filename = attachment_info.get('name')
        if not filename:
            filename = "attachment_" + str(attachment_info.get('id'))

        filepath = attachment_dir / filename

        # Write content to file
        with open(filepath, 'wb') as f:
            f.write(file_response.content)

        # Return path and attachment info
        return {
            "local_path": str(filepath.relative_to(output_dir.parent if isinstance(output_dir, Path) else Path(output_dir).parent)),
            "attachment_info": attachment_info
        }

    except Exception as e:
        print(f"Error downloading attachment {url}: {e}")
        return None

def save_issue_attachments(issue_number, attachments, output_dir):
    """Download and save all attachments for an issue"""
    saved_attachments = []
    issue_dir = Path(output_dir) / f"issue_{issue_number}"
    issue_dir.mkdir(parents=True, exist_ok=True)

    for attachment in attachments:
        attachment_id = attachment.get('id')
        if attachment_id:
            print(f"  Downloading issue attachment: {attachment.get('name')}")
            result = download_issue_attachment(issue_number, attachment_id, issue_dir)
            if result:
                saved_attachments.append(result)

    return saved_attachments

def save_comment_attachments(issue_number, comment_id, attachments, output_dir):
    """Download and save all attachments for a comment"""
    saved_attachments = []
    comment_dir = Path(output_dir) / f"issue_{issue_number}" / f"comment_{comment_id}"
    comment_dir.mkdir(parents=True, exist_ok=True)

    for attachment in attachments:
        attachment_id = attachment.get('id')
        if attachment_id:
            print(f"  Downloading comment attachment: {attachment.get('name')}")
            result = download_comment_attachment(comment_id, attachment_id, comment_dir)
            if result:
                saved_attachments.append(result)

    return saved_attachments

def export_all_issues(output_file, attachments_dir=None):
    issues_url = f"{GITEA_URL}/api/v1/repos/{OWNER}/{REPO}/issues"
    issues = get_paginated_data(issues_url, params={"state": "all"})

    exported_issues = []
    for issue in issues:
        issue_number = issue.get("number")
        print(f"Processing issue #{issue_number}: {issue.get('title')}")
        comments = get_comments(issue_number)
        issue_reactions = get_issue_reactions(issue_number)
        issue_dependencies = get_issue_dependencies(issue_number)

        # Download attachments if requested
        if attachments_dir:
            # Get and process issue attachments
            issue_attachments = get_issue_attachments(issue_number)
            if issue_attachments:
                print(f"  Found {len(issue_attachments)} attachments for issue #{issue_number}")
                downloaded_attachments = save_issue_attachments(issue_number, issue_attachments, attachments_dir)
                issue['attachments'] = issue_attachments
                issue['downloaded_attachments'] = downloaded_attachments

            # Process comments, fetch reactions and attachments
            for comment in comments:
                comment_id = comment.get("id")
                # Get comment reactions
                comment_reactions = get_comment_reactions(comment_id)
                comment["reactions"] = comment_reactions

                # Get and process comment attachments
                comment_attachments = get_comment_attachments(comment_id)
                if comment_attachments:
                    print(f"  Found {len(comment_attachments)} attachments for comment #{comment_id}")
                    downloaded_comment_attachments = save_comment_attachments(
                        issue_number, comment_id, comment_attachments, attachments_dir
                    )
                    comment['attachments'] = comment_attachments
                    comment['downloaded_attachments'] = downloaded_comment_attachments
        else:
            # Only fetch reactions for each comment
            for comment in comments:
                comment_id = comment.get("id")
                comment_reactions = get_comment_reactions(comment_id)
                comment["reactions"] = comment_reactions

        exported_issues.append({
            "issue": issue,
            "comments": comments,
            "reactions": issue_reactions,
            "dependencies": issue_dependencies
        })

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(exported_issues, f, indent=2)

    print(f"Exported {len(exported_issues)} issues to {output_file}")

# Parse command line arguments
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Export Gitea issues with comments, reactions, and attachments')
    parser.add_argument('--output', '-o', default="all_issues_export.json",
                        help='Output JSON file path (default: all_issues_export.json)')
    parser.add_argument('--attachments-dir', '-a', default=None,
                        help='Directory to save attachments (default: no attachments downloaded)')

    args = parser.parse_args()

    # Create attachments directory if specified
    if args.attachments_dir:
        os.makedirs(args.attachments_dir, exist_ok=True)
        print(f"Attachments will be saved to: {args.attachments_dir}")

    # Export issues
    export_all_issues(args.output, args.attachments_dir)
