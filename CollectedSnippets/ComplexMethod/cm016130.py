def download_and_extract_csvs(
    run_id: int,
    jobs: list[dict],
    attempt: int = 1,
    no_cache: bool = False,
) -> list[tuple[str, str]]:
    """Download artifacts and return list of (csv_filename, csv_content) pairs."""
    cache = get_cache_dir(run_id, attempt)
    results = []
    fetched = 0

    for job in jobs:
        # Check cache first
        cache_key = (
            f"{job['config']}-{job['shard']}-{job['num_shards']}-{job['job_id']}"
        )
        cache_marker = cache / f"{cache_key}.done"

        if not no_cache and cache_marker.exists():
            # Read cached CSVs
            for csv_file in cache.glob(f"{cache_key}__*.csv"):
                csv_name = csv_file.name.split("__", 1)[1]
                results.append((csv_name, csv_file.read_text()))
            continue

        url = s3_artifact_url(run_id, attempt, job)
        zip_path = cache / f"{cache_key}.zip"
        try:
            urllib.request.urlretrieve(url, str(zip_path))
            fetched += 1
        except urllib.error.HTTPError as e:
            print(
                f"  warning: failed to download shard {job['config']} "
                f"shard {job['shard']}: {e}",
                file=sys.stderr,
            )
            continue

        with zipfile.ZipFile(zip_path) as zf:
            for name in zf.namelist():
                if name.endswith("_performance.csv"):
                    csv_name = os.path.basename(name)
                    with zf.open(name) as f:
                        content = f.read().decode("utf-8")
                        results.append((csv_name, content))
                        # Write to cache
                        (cache / f"{cache_key}__{csv_name}").write_text(content)

        # Mark this shard as cached and remove the zip
        cache_marker.touch()
        zip_path.unlink(missing_ok=True)

    if fetched > 0:
        print(f"  downloaded {fetched} shards (cached at {cache})")
    elif results:
        print(f"  using cached data from {cache}")

    return results