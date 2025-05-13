# Gitea Import Export

Included are a couple of scripts to export and import issues from Gitea via the API.

Gitea includes command line tools to export the entire server as well as individual repositories, so this is perhaps redundant.

However, it's easy enough to migrate a git repo to another Gitea server using git itself, but it's not as easy to migrate issues, and if you don't have access to the command line tools, these scripts will fill a niche.

The export script has more features at the moment. It exports the following information:

- Issues
- Comments
- Labels
- Milestones
- Attachments (for issues and comments)
- Reactions (for issues and comments)
- Dependencies

The import script is not yet complete, but is included for reference.

## Environment Setup

A .env file is necessary with the following variables:
- GITEA_URL = http://gitea.example.com
- OWNER = owner
- REPO = repo
- TOKEN = Gitea API Key

## Usage

`python3 export_issues.py --help` to show the usage.
