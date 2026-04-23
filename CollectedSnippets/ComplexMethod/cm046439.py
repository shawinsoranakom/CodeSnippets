def github_releases(
    repo: str,
    *,
    per_page: int = 100,
    max_pages: int = 0,
) -> list[dict[str, Any]]:
    releases: list[dict[str, Any]] = []
    page = 1
    while True:
        payload = fetch_json(
            f"https://api.github.com/repos/{repo}/releases?per_page={per_page}&page={page}"
        )
        if not isinstance(payload, list):
            raise RuntimeError(f"unexpected releases payload for {repo}")
        page_items = [item for item in payload if isinstance(item, dict)]
        releases.extend(page_items)
        if len(payload) < per_page:
            break
        page += 1
        if max_pages > 0 and page > max_pages:
            break
    return releases