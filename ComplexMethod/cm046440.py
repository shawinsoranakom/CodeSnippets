def iter_release_payloads_by_time(
    repo: str,
    published_release_tag: str = "",
    requested_tag: str = "",
) -> Iterable[dict[str, Any]]:
    if published_release_tag:
        yield github_release(repo, published_release_tag)
        return

    if (
        requested_tag
        and requested_tag != "latest"
        and is_release_tag_like(requested_tag)
    ):
        try:
            yield github_release(repo, requested_tag)
            return
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                log(
                    f"release tag {requested_tag} not found in {repo}; scanning recent releases"
                )
            else:
                raise
        except Exception:
            raise

    releases = [
        release
        for release in github_releases(
            repo, max_pages = DEFAULT_GITHUB_RELEASE_SCAN_MAX_PAGES
        )
        if isinstance(release, dict)
        and not release.get("draft")
        and not release.get("prerelease")
    ]
    releases.sort(key = release_time_sort_key, reverse = True)
    for release in releases:
        yield release