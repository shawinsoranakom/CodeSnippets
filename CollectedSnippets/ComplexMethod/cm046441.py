def parse_direct_linux_release_bundle(
    repo: str, release: dict[str, Any]
) -> PublishedReleaseBundle | None:
    release_tag = release.get("tag_name")
    if not isinstance(release_tag, str) or not release_tag:
        return None

    assets = release_asset_map(release)
    artifacts: list[PublishedLlamaArtifact] = []
    inferred_labels: list[str] = []

    linux_asset_re = re.compile(
        r"^app-(?P<label>.+)-(?P<target>linux-x64(?:-cpu)?|linux-x64-(?:cuda12|cuda13)-(?:older|newer|portable))\.tar\.gz$"
    )
    for asset_name in sorted(assets):
        match = linux_asset_re.fullmatch(asset_name)
        if not match:
            continue
        inferred_labels.append(match.group("label"))
        target = match.group("target")
        if target in {"linux-x64", "linux-x64-cpu"}:
            artifacts.append(
                PublishedLlamaArtifact(
                    asset_name = asset_name,
                    install_kind = "linux-cpu",
                    runtime_line = None,
                    coverage_class = None,
                    supported_sms = [],
                    min_sm = None,
                    max_sm = None,
                    bundle_profile = None,
                    rank = 1000,
                )
            )
            continue

        bundle_profile = target.removeprefix("linux-x64-")
        profile = DIRECT_LINUX_BUNDLE_PROFILES.get(bundle_profile)
        if profile is None:
            continue
        artifacts.append(
            PublishedLlamaArtifact(
                asset_name = asset_name,
                install_kind = "linux-cuda",
                runtime_line = str(profile["runtime_line"]),
                coverage_class = str(profile["coverage_class"]),
                supported_sms = [str(value) for value in profile["supported_sms"]],
                min_sm = int(profile["min_sm"]),
                max_sm = int(profile["max_sm"]),
                bundle_profile = bundle_profile,
                rank = int(profile["rank"]),
            )
        )

    if not artifacts:
        return None

    upstream_tag = (
        release_tag
        if is_release_tag_like(release_tag)
        else inferred_labels[0]
        if len(set(inferred_labels)) == 1 and inferred_labels
        else release_tag
    )
    selection_log = [
        f"published_release: repo={repo}",
        f"published_release: tag={release_tag}",
        f"published_release: upstream_tag={upstream_tag}",
        "published_release: direct_asset_scan=linux",
    ]
    return PublishedReleaseBundle(
        repo = repo,
        release_tag = release_tag,
        upstream_tag = upstream_tag,
        assets = assets,
        manifest_asset_name = DEFAULT_PUBLISHED_MANIFEST_ASSET,
        artifacts = artifacts,
        selection_log = selection_log,
    )