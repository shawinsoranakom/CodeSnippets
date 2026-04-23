def source_build_plan_for_release(
    release: ResolvedPublishedRelease,
) -> SourceBuildPlan:
    checksums = release.checksums
    exact_source = exact_source_archive_hash(checksums)
    source_repo = checksums.source_repo or release.bundle.source_repo
    source_repo_url = checksums.source_repo_url or release.bundle.source_repo_url
    requested_source_ref = (
        checksums.requested_source_ref or release.bundle.requested_source_ref
    )
    resolved_source_ref = (
        checksums.resolved_source_ref or release.bundle.resolved_source_ref
    )
    source_commit = checksums.source_commit or release.bundle.source_commit
    source_ref_kind = checksums.source_ref_kind or release.bundle.source_ref_kind
    source_url = source_repo_clone_url(source_repo, source_repo_url)
    if exact_source is not None and source_url and source_commit:
        return SourceBuildPlan(
            source_url = source_url,
            source_ref = source_commit,
            source_ref_kind = "commit",
            compatibility_upstream_tag = release.bundle.upstream_tag,
            source_repo = source_repo,
            source_repo_url = source_repo_url,
            requested_source_ref = requested_source_ref,
            resolved_source_ref = resolved_source_ref,
            source_commit = source_commit,
        )
    source_ref = checkout_friendly_ref(
        source_ref_kind, resolved_source_ref or requested_source_ref
    )
    if (
        source_url
        and source_ref
        and source_ref_kind in {"tag", "branch", "pull", "commit"}
    ):
        return SourceBuildPlan(
            source_url = source_url,
            source_ref = source_ref,
            source_ref_kind = source_ref_kind,
            compatibility_upstream_tag = release.bundle.upstream_tag,
            source_repo = source_repo,
            source_repo_url = source_repo_url,
            requested_source_ref = requested_source_ref,
            resolved_source_ref = resolved_source_ref,
            source_commit = source_commit,
        )
    return SourceBuildPlan(
        source_url = source_url_from_repo_slug(UPSTREAM_REPO)
        or "https://github.com/ggml-org/llama.cpp",
        source_ref = release.bundle.upstream_tag,
        source_ref_kind = "tag",
        compatibility_upstream_tag = release.bundle.upstream_tag,
        source_repo = source_repo,
        source_repo_url = source_repo_url,
        requested_source_ref = requested_source_ref,
        resolved_source_ref = resolved_source_ref,
        source_commit = source_commit,
    )