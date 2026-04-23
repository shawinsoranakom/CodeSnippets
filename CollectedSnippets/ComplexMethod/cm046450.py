def iter_published_release_bundles(
    repo: str, published_release_tag: str = ""
) -> Iterable[PublishedReleaseBundle]:
    releases = (
        [github_release(repo, published_release_tag)]
        if published_release_tag
        else github_releases(repo, max_pages = DEFAULT_GITHUB_RELEASE_SCAN_MAX_PAGES)
    )
    for release in releases:
        if not published_release_tag and (
            release.get("draft") or release.get("prerelease")
        ):
            continue
        try:
            bundle = parse_published_release_bundle(repo, release)
        except Exception as exc:
            release_tag = release.get("tag_name", "unknown")
            log(f"published release metadata ignored for {repo}@{release_tag}: {exc}")
            continue
        if bundle is None:
            continue
        yield bundle