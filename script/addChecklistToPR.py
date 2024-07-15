import os
import base64
import requests
import json
import sys
import argparse
from typing import List

def get_github_token(token: str):
    if not token:
        print("GitHub token not provided.")
        sys.exit(1)
    return token

def extract_and_format_tags(pr_title: str) -> List[str]:
    import re
    match = re.search(r'RTImport-(.*)-RTChk', pr_title)
    if not match:
        return []
    tags_str = match.group(1).replace(', ', ',')
    tags = [tag.strip() for tag in tags_str.split(',')]
    return tags

def fetch_tags_file(token: str, file_base_url: str) -> str:
    url = f"{file_base_url}/tags.txt"
    headers = {'Authorization': f'token {token}'}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print("Failed to fetch tags.txt")
        sys.exit(1)
    content = response.json()['content']
    decoded_content = base64.b64decode(content).decode('utf-8')
    return decoded_content

def determine_task_files(tags: List[str], tags_file_content: str) -> List[str]:
    file_set = set()
    for line in tags_file_content.splitlines():
        tag_name, files = line.split('-')
        tag_name = tag_name.strip()
        files_list = [file.strip() for file in files.split(',')]
        if tag_name in tags:
            file_set.update(files_list)
    return list(file_set)

def post_comment_to_pr(token: str, repo: str, pr_number: int, content: str):
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {
        'Authorization': f'token {token}',
        'Content-Type': 'application/json'
    }
    data = {"body": content}
    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code != 201:
        print(f"Failed to post comment: {response.status_code}")
        print(response.json())
        sys.exit(1)

def main(pr_title: str, repo: str, pr_number: int, file_base_url: str, token: str):
    token = get_github_token(token)
    tags = extract_and_format_tags(pr_title)
    tags_file_content = fetch_tags_file(token, file_base_url)
    task_files = determine_task_files(tags, tags_file_content)
    
    for filename in task_files:
        encoded_filename = requests.utils.quote(filename)
        file_url = f"{file_base_url}/{encoded_filename}/{encoded_filename}.md"
        headers = {'Authorization': f'token {token}'}
        response = requests.get(file_url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch file {filename}")
            continue
        file_content = response.json()['content']
        decoded_content = base64.b64decode(file_content).decode('utf-8')
        post_comment_to_pr(token, repo, pr_number, decoded_content)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process PR details.')
    parser.add_argument('pr_title', type=str, help='Title of the Pull Request')
    parser.add_argument('repo', type=str, help='Repository name')
    parser.add_argument('pr_number', type=int, help='Pull Request number')
    parser.add_argument('file_base_url', type=str, help='Base URL for fetching files')
    parser.add_argument('token', type=str, help='GitHub Token')

    args = parser.parse_args()
    main(args.pr_title, args.repo, args.pr_number, args.file_base_url, args.token)
