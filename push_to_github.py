#!/usr/bin/env python3
"""
Push Distributed KV Store to GitHub using GitHub API
"""
import os
import json
import base64
import requests
from pathlib import Path

def push_to_github(github_token, username, repo_name):
    """
    Push local project files to GitHub using REST API
    """
    
    base_url = f"https://api.github.com/repos/{username}/{repo_name}"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }
    
    project_dir = Path(r"C:\Users\vikas\distributed-kv-store")
    
    # Step 1: Create repository
    print(f"[1] Creating repository '{repo_name}'...")
    create_repo_url = "https://api.github.com/user/repos"
    repo_data = {
        "name": repo_name,
        "description": "Distributed Key-Value Store with Consistent Hashing - Built with Python, TCP Sockets, and Multithreading",
        "private": False,
        "auto_init": True,
        "has_issues": True,
        "has_projects": True,
        "has_downloads": True
    }
    
    try:
        response = requests.post(create_repo_url, json=repo_data, headers=headers)
        if response.status_code in [201, 422]:  # 422 = already exists
            print(f"   Repository: {response.status_code}")
        else:
            print(f"   Error: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"   Error creating repo: {e}")
        return None
    
    # Step 2: Upload files
    print(f"\n[2] Uploading files...")
    files_to_upload = []
    
    for root, dirs, files in os.walk(project_dir):
        # Skip __pycache__ and .git
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', '.venv', 'venv']]
        
        for file in files:
            if file.endswith(('.py', '.md', '.txt', '.sh', '.bat')):
                file_path = Path(root) / file
                relative_path = file_path.relative_to(project_dir)
                files_to_upload.append(relative_path)
    
    print(f"   Found {len(files_to_upload)} files to upload")
    
    for file_path in files_to_upload:
        full_path = project_dir / file_path
        
        try:
            with open(full_path, 'rb') as f:
                content = f.read()
            
            # Encode content to base64
            encoded_content = base64.b64encode(content).decode('utf-8')
            
            upload_url = f"{base_url}/contents/{file_path}"
            upload_data = {
                "message": f"Add {file_path}",
                "content": encoded_content
            }
            
            response = requests.put(upload_url, json=upload_data, headers=headers)
            
            if response.status_code in [201, 200]:
                print(f"   OK: {file_path}")
            else:
                print(f"   FAILED: {file_path} ({response.status_code})")
        
        except Exception as e:
            print(f"   Error uploading {file_path}: {e}")
    
    print(f"\n[3] Complete!")
    repo_url = f"https://github.com/{username}/{repo_name}"
    print(f"   Repository URL: {repo_url}")
    return repo_url

def main():
    print("="*70)
    print("PUSH TO GITHUB - Interactive Setup")
    print("="*70)
    print()
    
    # Get credentials
    github_token = input("Enter your GitHub Personal Access Token: ").strip()
    if not github_token:
        print("Error: GitHub token required")
        return
    
    username = input("Enter your GitHub username: ").strip()
    if not username:
        print("Error: GitHub username required")
        return
    
    repo_name = input("Enter repository name (default: distributed-kv-store): ").strip()
    if not repo_name:
        repo_name = "distributed-kv-store"
    
    print()
    print(f"Pushing to: https://github.com/{username}/{repo_name}")
    print()
    
    repo_url = push_to_github(github_token, username, repo_name)
    
    if repo_url:
        print()
        print("="*70)
        print(f"SUCCESS! Your repository is at: {repo_url}")
        print("="*70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCancelled")
    except Exception as e:
        print(f"Error: {e}")
