def _validate_not_a_forked_repo(repo_owner, repo_name, ref):
    # Use urlopen to avoid depending on local git.
    headers = {"Accept": "application/vnd.github.v3+json"}
    token = os.environ.get(ENV_GITHUB_TOKEN)
    if token is not None:
        headers["Authorization"] = f"token {token}"
    for url_prefix in (
        f"https://api.github.com/repos/{repo_owner}/{repo_name}/branches",
        f"https://api.github.com/repos/{repo_owner}/{repo_name}/tags",
    ):
        page = 0
        while True:
            page += 1
            url = f"{url_prefix}?per_page=100&page={page}"
            try:
                response = json.loads(_read_url(Request(url, headers=headers)))
            except HTTPError:
                # Retry without token in case it had insufficient permissions.
                del headers["Authorization"]
                response = json.loads(_read_url(Request(url, headers=headers)))
            # Empty response means no more data to process
            if not response:
                break
            for br in response:
                if br["name"] == ref or br["commit"]["sha"].startswith(ref):
                    return

    raise ValueError(
        f"Cannot find {ref} in https://github.com/{repo_owner}/{repo_name}. "
        "If it's a commit from a forked repo, please call hub.load() with forked repo directly."
    )