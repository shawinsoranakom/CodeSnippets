def parse_approved_release_checksums(
    repo: str,
    release_tag: str,
    payload: Any,
) -> ApprovedReleaseChecksums:
    if not isinstance(payload, dict):
        raise RuntimeError(
            f"published checksum asset {DEFAULT_PUBLISHED_SHA256_ASSET} was not a JSON object"
        )
    validate_schema_version(
        payload,
        label = f"published checksum asset {DEFAULT_PUBLISHED_SHA256_ASSET}",
    )
    if payload.get("component") != "llama.cpp":
        raise RuntimeError(
            f"published checksum asset {DEFAULT_PUBLISHED_SHA256_ASSET} did not describe llama.cpp"
        )
    payload_release_tag = payload.get("release_tag")
    if not isinstance(payload_release_tag, str) or not payload_release_tag:
        raise RuntimeError(
            f"published checksum asset {DEFAULT_PUBLISHED_SHA256_ASSET} omitted release_tag"
        )
    if payload_release_tag != release_tag:
        raise RuntimeError(
            f"published checksum asset {DEFAULT_PUBLISHED_SHA256_ASSET} release_tag={payload_release_tag} "
            f"did not match pinned release tag {release_tag}"
        )
    upstream_tag = payload.get("upstream_tag")
    if not isinstance(upstream_tag, str) or not upstream_tag:
        raise RuntimeError(
            f"published checksum asset {DEFAULT_PUBLISHED_SHA256_ASSET} omitted upstream_tag"
        )
    artifacts_payload = payload.get("artifacts")
    if not isinstance(artifacts_payload, dict):
        raise RuntimeError(
            f"published checksum asset {DEFAULT_PUBLISHED_SHA256_ASSET} omitted artifacts"
        )

    artifacts: dict[str, ApprovedArtifactHash] = {}
    for asset_name, raw_entry in artifacts_payload.items():
        if not isinstance(asset_name, str) or not asset_name:
            raise RuntimeError(
                "published checksum asset used a non-string artifact key"
            )
        if not isinstance(raw_entry, dict):
            raise RuntimeError(
                f"published checksum entry for {asset_name} was not an object"
            )
        digest = normalize_sha256_digest(raw_entry.get("sha256"))
        if not digest:
            raise RuntimeError(
                f"published checksum entry for {asset_name} omitted a valid sha256"
            )
        repo_value = raw_entry.get("repo")
        kind_value = raw_entry.get("kind")
        artifacts[asset_name] = ApprovedArtifactHash(
            asset_name = asset_name,
            sha256 = digest,
            repo = repo_value if isinstance(repo_value, str) and repo_value else None,
            kind = kind_value if isinstance(kind_value, str) and kind_value else None,
        )

    source_commit = normalize_source_commit(payload.get("source_commit"))
    source_commit_short = payload.get("source_commit_short")
    source_repo = payload.get("source_repo")
    source_repo_url = payload.get("source_repo_url")
    source_ref_kind = normalize_source_ref_kind(payload.get("source_ref_kind"))
    requested_source_ref = payload.get("requested_source_ref")
    resolved_source_ref = payload.get("resolved_source_ref")
    return ApprovedReleaseChecksums(
        repo = repo,
        release_tag = release_tag,
        upstream_tag = upstream_tag,
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
        artifacts = artifacts,
    )