import sys
import requests
import time
import json
import os
import base64
from termcolor import colored
import gitignore_parser


def delete_github_repo(name, github_username, token):
    url = f"https://api.github.com/repos/{github_username}/{name}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.delete(url, headers=headers)
    if response.status_code == 204:
        print(colored(f"Successfully deleted GitHub repository: {name}", "yellow"))
    else:
        error_message = response.json()["message"]
        print(colored(f"Failed to delete GitHub repository: {error_message}", "red"))


def create_github_repo(name, token):
    url = "https://api.github.com/user/repos"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    payload = json.dumps({"name": name, "private": False})
    response = requests.post(url, headers=headers, data=payload.encode("utf-8"))
    if response.status_code == 201:
        print(colored(f"Successfully created new GitHub repository: {name}", "green"))
        return True
    else:
        error_message = response.json()["message"]
        print(colored(f"Failed to create GitHub repository: {error_message}", "red"))
        return False


def add_files_to_github_repo(name, github_username, token, directory_path, matches):
    url = f"https://api.github.com/repos/{github_username}/{name}/contents/"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        if os.path.isfile(file_path):
            if matches(file_path):
                print(colored(f"File '{filename}' ignored by .gitignore.", "yellow"))
                continue
            with open(file_path, "rb") as f:
                content_bytes = f.read()
            content_str = base64.b64encode(content_bytes).decode("utf-8")
            payload = json.dumps({"message": f"add {filename}", "content": content_str})
            response = requests.put(url+filename, headers=headers, auth=(github_username, token), data=payload.encode("utf-8"))
            if response.status_code == 201:
                print(colored(f"Successfully added file to GitHub repository: {filename}", "green"))
            else:
                error_message = response.json()["message"]
                print(colored(f"Failed to add file to GitHub repository: {error_message}", "red"))
                # delete repository and exit if file upload fails
                delete_github_repo(name, github_username, token)
                sys.exit(1)
        else:
            add_files_to_github_repo(name, github_username, token, file_path)


def main():
    if len(sys.argv) != 5:
        print("Usage: python create_github_repo.py [repository_name] [directory_path] [github_username] [github_token]")
        sys.exit(1)
    else:
        # get command line arguments
        repo_name = sys.argv[1]
        directory_path = sys.argv[2]
        github_username = sys.argv[3]
        github_token = sys.argv[4]
        matches = gitignore_parser.parse_gitignore(directory_path+"/.gitignore")
    

        # create new GitHub repository
        success = create_github_repo(repo_name, github_token)
        if success:
            # add files to GitHub repository
            add_files_to_github_repo(repo_name, github_username, github_token, directory_path, matches)


if __name__ == "__main__":
    main()
