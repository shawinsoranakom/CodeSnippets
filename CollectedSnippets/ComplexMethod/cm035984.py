def infer_repo_from_message(user_msg: str) -> list[str]:
    """
    Extract all repository names in the format 'owner/repo' from various Git provider URLs
    and direct mentions in text. Supports GitHub, GitLab, and BitBucket.
    """
    normalized_msg = re.sub(r'\s+', ' ', user_msg.strip())

    git_url_pattern = (
        r'https?://(?:github\.com|gitlab\.com|bitbucket\.org)/'
        r'([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+?)(?:\.git)?'
        r'(?:[/?#].*?)?(?=\s|$|[^\w.-])'
    )

    # UPDATED: allow {{ owner/repo }} in addition to existing boundaries
    direct_pattern = (
        r'(?:^|\s|{{|[\[\(\'":`])'  # left boundary
        r'([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+)'
        r'(?=\s|$|}}|[\]\)\'",.:`])'  # right boundary
    )

    # Use dict to preserve ordering
    matches: dict[str, bool] = {}

    # Git URLs first (highest priority)
    for owner, repo in re.findall(git_url_pattern, normalized_msg):
        repo = re.sub(r'\.git$', '', repo)
        matches[f'{owner}/{repo}'] = True

    # Direct mentions
    for owner, repo in re.findall(direct_pattern, normalized_msg):
        full_match = f'{owner}/{repo}'

        if (
            re.match(r'^\d+\.\d+/\d+\.\d+$', full_match)
            or re.match(r'^\d{1,2}/\d{1,2}$', full_match)
            or re.match(r'^[A-Z]/[A-Z]$', full_match)
            or repo.endswith(('.txt', '.md', '.py', '.js'))
            or ('.' in repo and len(repo.split('.')) > 2)
        ):
            continue

        if full_match not in matches:
            matches[full_match] = True

    result = list(matches)
    return result