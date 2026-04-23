def resolve_published_release(
    requested_tag: str | None,
    published_repo: str,
    published_release_tag: str = "",
) -> ResolvedPublishedRelease:
    repo = published_repo or DEFAULT_PUBLISHED_REPO
    normalized_requested = normalized_requested_llama_tag(requested_tag)

    if published_release_tag:
        bundle = pinned_published_release_bundle(repo, published_release_tag)
        if not published_release_matches_request(bundle, normalized_requested):
            raise PrebuiltFallback(
                "published release "
                f"{repo}@{published_release_tag} targeted upstream tag {bundle.upstream_tag}, "
                f"but requested {normalized_requested}"
            )
        return ResolvedPublishedRelease(
            bundle = bundle,
            checksums = validated_checksums_for_bundle(repo, bundle),
        )

    skipped_invalid = 0
    for bundle in iter_published_release_bundles(repo):
        if not published_release_matches_request(bundle, normalized_requested):
            continue
        try:
            checksums = validated_checksums_for_bundle(repo, bundle)
        except PrebuiltFallback as exc:
            skipped_invalid += 1
            log(
                "published release ignored for install resolution: "
                f"{repo}@{bundle.release_tag} ({exc})"
            )
            continue
        return ResolvedPublishedRelease(bundle = bundle, checksums = checksums)

    if normalized_requested == "latest":
        if skipped_invalid:
            raise PrebuiltFallback(
                f"no usable published llama.cpp releases were available in {repo}"
            )
        raise PrebuiltFallback(
            f"no published llama.cpp releases were available in {repo}"
        )

    raise PrebuiltFallback(
        f"no published prebuilt release in {repo} matched upstream tag {normalized_requested}"
    )