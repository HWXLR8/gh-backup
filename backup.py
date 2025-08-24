#!/usr/bin/env python3

import requests
import subprocess
import os

GITHUB_USERNAME = ""
GITHUB_TOKEN = ""
BACKUP_DIR = ""

url = "https://api.github.com/user/repos?per_page=100"
headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

os.makedirs(BACKUP_DIR, exist_ok=True)

urepos = set() # unique repos

timestamp = datetime.datetime.now()
print(f"backing up github.com/{GITHUB_USERNAME} @ {timestamp}")
while url:
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"error: {response.status_code} - {response.text}")
        break

    repos = response.json()

    for repo in repos:
        repo_name = repo["name"]
        repo_url = repo["clone_url"]
        is_private = repo["private"]
        is_fork = repo["fork"]

        # github API bug, sometimes reports duplicate repos
        if repo_name in urepos:
            print(f"duplicate detected: {repo_name}")
            continue

        urepos.add(repo_name)

        dir = os.path.join(BACKUP_DIR, repo_name)

        # clone repo if not exist
        if not os.path.exists(dir):
            print(f"cloning {'private' if is_private else 'public'} repo: {repo_name}")
            # add token to url
            token_repo_url = f"https://{GITHUB_TOKEN}:x-oauth-basic@{repo_url.replace('https://', '')}"
            subprocess.run(["git", "clone", "--mirror", token_repo_url, dir])
        else: # update repo if exists
            print(f"updating existing repo: {repo_name}")
            os.chdir(dir)
            try:
                # fetch updates from all remotes and all branches
                subprocess.run(["git", "fetch", "--all"], check=True)
                # update all refs
                subprocess.run(["git", "remote", "update"], check=True)
            except subprocess.CalledProcessError as e:
                print(f"error updating {repo_name}: {e}")
            finally:
                # Change back to the original directory
                os.chdir(BACKUP_DIR)

    url = response.links.get("next", {}).get("url")
