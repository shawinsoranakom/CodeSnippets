def parse_published_release_bundle(
    repo: str, release: dict[str, Any]
) -> PublishedReleaseBundle | None:
    release_tag = release.get("tag_name")
    if not isinstance(release_tag, str) or not release_tag:
        return None

    assets = release_asset_map(release)
    manifest_url = assets.get(DEFAULT_PUBLISHED_MANIFEST_ASSET)
    if not manifest_url:
        return None

    # Mixed repos are filtered by an explicit release-side manifest rather than
    # by release tag or asset filename conventions.
    manifest_bytes = download_bytes(
        manifest_url,
        timeout = 30,
        headers = auth_headers(manifest_url),
    )
    manifest_sha256 = sha256_bytes(manifest_bytes)
    try:
        manifest_payload = json.loads(manifest_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"published manifest {DEFAULT_PUBLISHED_MANIFEST_ASSET} was not valid JSON"
        ) from exc
    if not isinstance(manifest_payload, dict):
        raise RuntimeError(
            f"published manifest {DEFAULT_PUBLISHED_MANIFEST_ASSET} was not a JSON object"
        )
    validate_schema_version(
        manifest_payload,
        label = f"published manifest {DEFAULT_PUBLISHED_MANIFEST_ASSET} in {repo}@{release_tag}",
    )
    component = manifest_payload.get("component")
    upstream_tag = manifest_payload.get("upstream_tag")
    source_repo = manifest_payload.get("source_repo")
    source_repo_url = manifest_payload.get("source_repo_url")
    source_ref_kind = normalize_source_ref_kind(manifest_payload.get("source_ref_kind"))
    requested_source_ref = manifest_payload.get("requested_source_ref")
    resolved_source_ref = manifest_payload.get("resolved_source_ref")
    source_commit = normalize_source_commit(manifest_payload.get("source_commit"))
    source_commit_short = manifest_payload.get("source_commit_short")
    if component != "llama.cpp":
        return None
    if not isinstance(upstream_tag, str) or not upstream_tag:
        raise RuntimeError(
            f"published manifest {DEFAULT_PUBLISHED_MANIFEST_ASSET} in {repo}@{release_tag} omitted upstream_tag"
        )

    artifacts_payload = manifest_payload.get("artifacts")
    if not isinstance(artifacts_payload, list):
        raise RuntimeError(
            f"published manifest {DEFAULT_PUBLISHED_MANIFEST_ASSET} in {repo}@{release_tag} omitted artifacts"
        )

    artifacts: list[PublishedLlamaArtifact] = []
    for index, raw_artifact in enumerate(artifacts_payload):
        try:
            artifact = parse_published_artifact(raw_artifact)
        except ValueError as exc:
            log(
                f"published artifact ignored for {repo}@{release_tag} artifact[{index}]: {exc}"
            )
            continue
        if artifact is not None:
            artifacts.append(artifact)
    selection_log = [
        f"published_release: repo={repo}",
        f"published_release: tag={release_tag}",
        f"published_release: manifest={DEFAULT_PUBLISHED_MANIFEST_ASSET}",
        f"published_release: upstream_tag={upstream_tag}",
    ]
    if isinstance(source_repo, str) and source_repo:
        selection_log.append(f"published_release: source_repo={source_repo}")
    if source_commit:
        selection_log.append(f"published_release: source_commit={source_commit}")
    return PublishedReleaseBundle(
        repo = repo,
        release_tag = release_tag,
        upstream_tag = upstream_tag,
        manifest_sha256 = manifest_sha256,
        source_repo = source_repo
        if isinstance(source_repo, str) and source_repo
        else None,
        source_repo_url = source_repo_url
        if isinstance(source_repo_url, str) and source_repo_url
        else None,
        source_ref_kind = source_ref_kind,
        requested_source_ref = requested_source_ref
        if isinstance(requested_source_ref, str) and requested_source_ref
        else None,
        resolved_source_ref = resolved_source_ref
        if isinstance(resolved_source_ref, str) and resolved_source_ref
        else None,
        source_commit = source_commit,
        source_commit_short = source_commit_short
        if isinstance(source_commit_short, str) and source_commit_short
        else None,
        assets = assets,
        manifest_asset_name = DEFAULT_PUBLISHED_MANIFEST_ASSET,
        artifacts = artifacts,
        selection_log = selection_log,
    )