import os
import requests
import json

# Bitbucket settings
WORKSPACE = 'SP'
USERNAME = os.environ.get('BITBUCKET_USERNAME')
API_TOKEN = os.environ.get('BITBUCKET_API_TOKEN')
URL = os.environ.get('BITBUCKET_API_URL')

# Pull Request settings
SOURCE_BRANCH = 'master'
TITLE = 'Master sync'
DESCRIPTION = 'Sync master into branch'


class InputKeys(object):
    REVIEWERS = 'Reviewers:'
    REPOS = 'Repositories:'


class Modes(object):
    REVIEWERS = 'reviewers'
    REPOS = 'repos'


def get_config():
    # Read config file
    with open('config.txt', 'r') as file:
        lines = file.readlines()

    mode = 'none'
    reviewers = []
    repos = []
    for line in lines:
        stripped_line = line.strip()
        if len(stripped_line) == 0:
            continue
        elif stripped_line.lower() == InputKeys.REVIEWERS.lower():
            mode = Modes.REVIEWERS
        elif stripped_line.lower() == InputKeys.REPOS.lower():
            mode = Modes.REPOS
        elif mode == Modes.REVIEWERS:
            reviewers.extend(split_string_on_whitespace(stripped_line))
        elif mode == Modes.REPOS:
            branch, repo = split_string_on_whitespace(stripped_line)
            repos.append((branch, repo))

    return reviewers, repos


def split_string_on_whitespace(input):
    return [item for item in input.split(' ') if item != '']


def create_pull_request(branch, repo, reviewers, links, errors):
    # Create Pull Request payload
    if len(reviewers) == 0:
        payload = \
        {
            "title": TITLE,
            "fromRef": {
                "id": f"refs/heads/{SOURCE_BRANCH}"
            },
            "toRef": {
                "id": f"refs/heads/{branch}"
            },
            "description": DESCRIPTION
        }
    else:
        payload = \
        {
            "title": TITLE,
            "fromRef": {
                "id": f"refs/heads/{SOURCE_BRANCH}"
            },
            "toRef": {
                "id": f"refs/heads/{branch}"
            },
            "description": DESCRIPTION,
            "reviewers": [{"user": {"name": reviewer}} for reviewer in reviewers]
        }

    # Make the API request to create the pull request
    url = URL.format(project_key=WORKSPACE, repo_slug=repo)
    print(f"Creating PR for repo: {repo} to sync {branch} to master")
    response = requests.post(
        url,
        auth=(USERNAME, API_TOKEN),
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload),
        verify=False
    )

    # Check if the request was successful
    if response.status_code == 201:
        print("Pull request created successfully.")
        pr_data = response.json()
        print(f"PR Link: {pr_data['links']['self'][0]['href']}")
        links.append((repo, pr_data['links']['self'][0]['href']))
    else:
        print(f"Failed to create pull request. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        errors.append((repo, response.status_code, response.text))


_reviewers, _repos = get_config()

links = []
errors = []
for _branch, _repo in _repos:
    create_pull_request(branch=_branch, repo=_repo, reviewers=_reviewers, links=links, errors=errors)
    
print("List complete!")
print("Error list:")
for repo, code, message in errors:
    print(f"{repo}: [{code}] {message}")

print("Links:")
for repo, link in links:
    print(f"{repo}: {link}")