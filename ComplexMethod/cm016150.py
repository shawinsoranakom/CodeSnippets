def download_single_artifact(suite, shard, url_candidates):
    """Download a single artifact, trying each URL candidate until one succeeds.

    Returns a tuple of (suite, shard, result_dict) where result_dict maps
    (suite, phase) -> DataFrame, or None if download failed.
    """
    subsuite = normalize_suite_filename(suite)
    for url in url_candidates:
        try:
            resp = urlopen(url)
            artifact = ZipFile(BytesIO(resp.read()))
            result = {}
            for phase in ("training", "inference"):
                # Try both paths - CUDA uses test/test-reports/, ROCm uses test-reports/
                possible_names = [
                    f"test/test-reports/{phase}_{subsuite}.csv",
                    f"test-reports/{phase}_{subsuite}.csv",
                ]
                found = False
                for name in possible_names:
                    try:
                        df = pd.read_csv(artifact.open(name))
                        df["graph_breaks"] = df["graph_breaks"].fillna(0).astype(int)
                        result[(suite, phase)] = df
                        found = True
                        break
                    except KeyError:
                        continue
                if not found and phase == "inference":
                    # No warning for training, since it's expected to be missing for some tests
                    print(
                        f"Warning: Unable to find {phase}_{subsuite}.csv in artifacts file from {url}, continuing"
                    )
            return (suite, shard, result)
        except urllib.error.HTTPError:
            continue  # Try next candidate URL
    return (suite, shard, None)