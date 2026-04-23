def _load_disabled_vllm_tests_from_github() -> list[dict[str, Any]]:
    if not _DISABLED_VLLM_TESTS_ISSUE:
        return []
    url = f"https://api.github.com/repos/pytorch/pytorch/issues/{_DISABLED_VLLM_TESTS_ISSUE}"
    headers = {"Accept": "application/vnd.github.v3+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            issue = json.loads(resp.read())
        body = issue.get("body", "") or ""
        entries = _parse_disabled_tests_from_issue_body(body)
        # Filter out malformed entries — the issue body is user-editable
        entries = [e for e in entries if "test" in e]
        issue_url = issue.get("html_url", url)
        for entry in entries:
            entry.setdefault("issue", issue_url)
        return entries
    except Exception:
        logger.warning(
            "Failed to fetch disabled vLLM tests from GitHub issue #%d",
            _DISABLED_VLLM_TESTS_ISSUE,
            exc_info=True,
        )
        return []