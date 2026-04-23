def main() -> None:
    """Fetch GitHub stars for all repos in README.md, updating the JSON cache."""
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        print("Error: GITHUB_TOKEN environment variable is required.", file=sys.stderr)
        sys.exit(1)

    readme_text = README_PATH.read_text(encoding="utf-8")
    current_repos = extract_github_repos(readme_text)
    current_repos.add("vinta/awesome-python")
    print(f"Found {len(current_repos)} GitHub repos in README.md")

    cache = load_stars(CACHE_FILE)
    now = datetime.now(UTC)

    # Prune entries not in current README
    pruned = {k: v for k, v in cache.items() if k in current_repos}
    if len(pruned) < len(cache):
        print(f"Pruned {len(cache) - len(pruned)} stale cache entries")
    cache = pruned

    # Determine which repos need fetching (missing or stale)
    max_age = timedelta(hours=CACHE_MAX_AGE_HOURS)
    to_fetch = []
    for repo in sorted(current_repos):
        entry = cache.get(repo)
        if entry and "fetched_at" in entry:
            fetched = datetime.fromisoformat(entry["fetched_at"])
            if now - fetched < max_age:
                continue
        to_fetch.append(repo)

    print(f"{len(to_fetch)} repos to fetch ({len(current_repos) - len(to_fetch)} cached)")

    if not to_fetch:
        save_cache(cache)
        print("Cache is up to date.")
        return

    # Fetch in batches
    fetched_count = 0
    skipped_repos: list[str] = []

    now_iso = now.isoformat()
    total_batches = (len(to_fetch) + BATCH_SIZE - 1) // BATCH_SIZE

    with httpx.Client(
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
        transport=httpx.HTTPTransport(retries=2),
        timeout=30,
    ) as client:
        for batch_num, batch in enumerate(batched(to_fetch, BATCH_SIZE), 1):
            print(f"Fetching batch {batch_num}/{total_batches} ({len(batch)} repos)...")

            try:
                results = fetch_batch(batch, client)
            except httpx.HTTPStatusError as e:
                print(f"HTTP error {e.response.status_code}", file=sys.stderr)
                if e.response.status_code == 401:
                    print("Error: Invalid GITHUB_TOKEN.", file=sys.stderr)
                    sys.exit(1)
                print("Saving partial cache and exiting.", file=sys.stderr)
                save_cache(cache)
                sys.exit(1)

            for repo in batch:
                if repo in results:
                    cache[repo] = {**results[repo], "fetched_at": now_iso}
                    fetched_count += 1
                else:
                    skipped_repos.append(repo)

            # Save after each batch in case of interruption
            save_cache(cache)

    if skipped_repos:
        print(f"Skipped {len(skipped_repos)} repos (deleted/private/renamed)")
    print(f"Done. Fetched {fetched_count} repos, {len(cache)} total cached.")