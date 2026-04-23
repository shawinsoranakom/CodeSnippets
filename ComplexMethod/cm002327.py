def get_commit_info(commit, pr_number=None):
    """Get information for a commit via `api.github.com`."""
    if commit is None:
        return {"commit": None, "pr_number": None, "author": None, "merged_by": None}

    author = None
    merged_author = None

    # Use PR number from environment if not provided
    if pr_number is None:
        pr_number = os.environ.get("pr_number")

    # First, get commit info to check if it's a merge commit
    url = f"https://api.github.com/repos/huggingface/transformers/commits/{commit}"
    commit_info = requests.get(url).json()

    commit_to_query = commit

    # Check if this is a merge commit created by GitHub
    if commit_info.get("parents") and len(commit_info["parents"]) > 1:
        commit_message = commit_info.get("commit", {}).get("message", "")
        # Parse message like "Merge 1ac46bed... into 5a67f0a7..."
        import re

        match = re.match(r"^Merge ([a-f0-9]{40}) into ([a-f0-9]{40})", commit_message)
        if match:
            # Use the first SHA (the PR commit)
            commit_to_query = match.group(1)

    # If no PR number yet, try to discover it from the commit
    if not pr_number:
        url = f"https://api.github.com/repos/huggingface/transformers/commits/{commit_to_query}/pulls"
        pr_info_for_commit = requests.get(url).json()
        if len(pr_info_for_commit) > 0:
            pr_number = pr_info_for_commit[0]["number"]

    # If we have a PR number, get author and merged_by info
    if pr_number:
        url = f"https://api.github.com/repos/huggingface/transformers/pulls/{pr_number}"
        pr_for_commit = requests.get(url).json()
        author = pr_for_commit["user"]["login"]
        if pr_for_commit["merged_by"] is not None:
            merged_author = pr_for_commit["merged_by"]["login"]

    parent = commit_info["parents"][0]["sha"]
    if author is None:
        author = commit_info["author"]["login"]

    return {"commit": commit, "pr_number": pr_number, "author": author, "merged_by": merged_author, "parent": parent}