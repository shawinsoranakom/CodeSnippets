def resolve_release_asset_choice(
    host: HostInfo,
    llama_tag: str,
    release: PublishedReleaseBundle,
    checksums: ApprovedReleaseChecksums,
) -> list[AssetChoice]:
    if host.is_windows and host.is_x86_64 and host.has_usable_nvidia:
        torch_preference = detect_torch_cuda_runtime_preference(host)
        published_attempts = published_windows_cuda_attempts(
            host,
            release,
            torch_preference.runtime_line,
            torch_preference.selection_log,
        )
        if published_attempts:
            try:
                return apply_approved_hashes(published_attempts, checksums)
            except PrebuiltFallback as exc:
                log(
                    "published Windows CUDA assets ignored for install planning: "
                    f"{release.repo}@{release.release_tag} ({exc})"
                )
        upstream_assets = github_release_assets(UPSTREAM_REPO, llama_tag)
        return apply_approved_hashes(
            resolve_windows_cuda_choices(host, llama_tag, upstream_assets),
            checksums,
        )

    published_choice: AssetChoice | None = None
    if host.is_windows and host.is_x86_64:
        # AMD Windows hosts should prefer a hash-approved published
        # Windows HIP bundle when one exists, but otherwise fall through
        # to resolve_asset_choice() so the upstream HIP prebuilt is
        # tried before the CPU fallback. Hard-pinning the published
        # windows-cpu bundle here would make the new HIP path
        # unreachable.
        if host.has_rocm:
            published_choice = published_asset_choice_for_kind(release, "windows-hip")
        else:
            published_choice = published_asset_choice_for_kind(release, "windows-cpu")
    elif host.is_macos and host.is_arm64:
        published_choice = published_asset_choice_for_kind(release, "macos-arm64")
    elif host.is_macos and host.is_x86_64:
        published_choice = published_asset_choice_for_kind(release, "macos-x64")

    if published_choice is not None:
        try:
            return apply_approved_hashes([published_choice], checksums)
        except PrebuiltFallback as exc:
            log(
                "published platform asset ignored for install planning: "
                f"{release.repo}@{release.release_tag} {published_choice.name} ({exc})"
            )

    return apply_approved_hashes([resolve_asset_choice(host, llama_tag)], checksums)