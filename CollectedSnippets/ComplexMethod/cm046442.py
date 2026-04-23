def direct_upstream_release_plan(
    release: dict[str, Any],
    host: HostInfo,
    repo: str,
    requested_tag: str,
) -> InstallReleasePlan | None:
    release_tag = release.get("tag_name")
    if not isinstance(release_tag, str) or not release_tag:
        return None
    if not direct_release_matches_request(
        release_tag = release_tag,
        llama_tag = release_tag,
        requested_tag = requested_tag,
    ):
        return None

    assets = release_asset_map(release)
    attempts: list[AssetChoice] = []
    if host.is_windows and host.is_x86_64:
        if host.has_usable_nvidia:
            torch_preference = detect_torch_cuda_runtime_preference(host)
            attempts.extend(
                windows_cuda_attempts(
                    host,
                    release_tag,
                    assets,
                    torch_preference.runtime_line,
                    torch_preference.selection_log,
                )
            )
        cpu_asset = f"llama-{release_tag}-bin-win-cpu-x64.zip"
        cpu_url = assets.get(cpu_asset)
        if cpu_url:
            attempts.append(
                AssetChoice(
                    repo = repo,
                    tag = release_tag,
                    name = cpu_asset,
                    url = cpu_url,
                    source_label = "upstream",
                    install_kind = "windows-cpu",
                )
            )
    elif host.is_macos and host.is_arm64:
        asset_name = f"llama-{release_tag}-bin-macos-arm64.tar.gz"
        asset_url = assets.get(asset_name)
        if asset_url:
            attempts.append(
                AssetChoice(
                    repo = repo,
                    tag = release_tag,
                    name = asset_name,
                    url = asset_url,
                    source_label = "upstream",
                    install_kind = "macos-arm64",
                )
            )
    elif host.is_macos and host.is_x86_64:
        asset_name = f"llama-{release_tag}-bin-macos-x64.tar.gz"
        asset_url = assets.get(asset_name)
        if asset_url:
            attempts.append(
                AssetChoice(
                    repo = repo,
                    tag = release_tag,
                    name = asset_name,
                    url = asset_url,
                    source_label = "upstream",
                    install_kind = "macos-x64",
                )
            )
    elif host.is_linux and host.is_x86_64 and not host.has_usable_nvidia:
        asset_name = f"llama-{release_tag}-bin-ubuntu-x64.tar.gz"
        asset_url = assets.get(asset_name)
        if asset_url:
            attempts.append(
                AssetChoice(
                    repo = repo,
                    tag = release_tag,
                    name = asset_name,
                    url = asset_url,
                    source_label = "upstream",
                    install_kind = "linux-cpu",
                )
            )
    if not attempts:
        raise PrebuiltFallback("no compatible upstream prebuilt asset was found")
    return InstallReleasePlan(
        requested_tag = requested_tag,
        llama_tag = release_tag,
        release_tag = release_tag,
        attempts = attempts,
        approved_checksums = synthetic_checksums_for_release(
            repo,
            release_tag,
            release_tag,
        ),
    )