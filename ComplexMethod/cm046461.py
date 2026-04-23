def resolve_upstream_asset_choice(host: HostInfo, llama_tag: str) -> AssetChoice:
    upstream_assets = github_release_assets(UPSTREAM_REPO, llama_tag)
    if host.is_linux and host.is_x86_64:
        # AMD ROCm: try upstream ROCm prebuilt first, then fall back to source build.
        # Source build (via setup.sh) compiles with -DGGML_HIP=ON and auto-detects
        # the exact GPU target via rocminfo, which is more reliable for consumer
        # GPUs (e.g. gfx1151) that may not be in the prebuilt.
        if host.has_rocm and not host.has_usable_nvidia:
            # Scan upstream assets for any rocm-<version> prebuilt. When the
            # host ROCm runtime version is known, pick the newest candidate
            # whose major.minor is <= host version -- otherwise a ROCm 6.4
            # host would download the rocm-7.2 tarball, fail preflight, and
            # fall back to a source build even though a compatible 6.4
            # prebuilt exists. If no compatible candidate matches (e.g. host
            # runtime is older than every published prebuilt), fall back to
            # the numerically newest so we at least try something.
            _rocm_pattern = re.compile(
                rf"llama-{re.escape(llama_tag)}-bin-ubuntu-rocm-([0-9]+(?:\.[0-9]+)*)-x64\.tar\.gz"
            )
            rocm_candidates: list[tuple[tuple[int, ...], str]] = []
            for _name in upstream_assets:
                _m = _rocm_pattern.match(_name)
                if _m is None:
                    continue
                _parts = tuple(int(p) for p in _m.group(1).split("."))
                rocm_candidates.append((_parts, _name))
            rocm_candidates.sort(reverse = True)
            _host_rocm_version = _detect_host_rocm_version()
            _compatible: list[tuple[tuple[int, ...], str]] = rocm_candidates
            if _host_rocm_version is not None:
                _compatible = [
                    item
                    for item in rocm_candidates
                    if item[0][:2] <= _host_rocm_version
                ]
            if rocm_candidates and not _compatible:
                # Fall back to the newest candidate so a source build is
                # not forced when the host runtime is older than every
                # published prebuilt: preflight will still catch a true
                # incompatibility and trigger a fallback.
                _compatible = rocm_candidates[:1]
            if _compatible:
                rocm_name = _compatible[0][1]
                if _host_rocm_version is not None:
                    log(
                        f"AMD ROCm {_host_rocm_version[0]}.{_host_rocm_version[1]} "
                        f"detected -- trying upstream prebuilt {rocm_name}"
                    )
                else:
                    log(f"AMD ROCm detected -- trying upstream prebuilt {rocm_name}")
                log(
                    "Note: if your ROCm runtime version differs significantly, "
                    "this may fail preflight and fall back to a source build (safe)"
                )
                return AssetChoice(
                    repo = UPSTREAM_REPO,
                    tag = llama_tag,
                    name = rocm_name,
                    url = upstream_assets[rocm_name],
                    source_label = "upstream",
                    install_kind = "linux-rocm",
                )
            # No ROCm prebuilt available -- fall back to source build
            raise PrebuiltFallback(
                "AMD ROCm detected but no upstream ROCm prebuilt found; "
                "falling back to source build with HIP support"
            )

        upstream_name = f"llama-{llama_tag}-bin-ubuntu-x64.tar.gz"
        if upstream_name not in upstream_assets:
            raise PrebuiltFallback("upstream Linux CPU asset was not found")
        return AssetChoice(
            repo = UPSTREAM_REPO,
            tag = llama_tag,
            name = upstream_name,
            url = upstream_assets[upstream_name],
            source_label = "upstream",
            install_kind = "linux-cpu",
        )

    if host.is_windows and host.is_x86_64:
        if host.has_usable_nvidia:
            attempts = resolve_windows_cuda_choices(host, llama_tag, upstream_assets)
            if attempts:
                return attempts[0]
            raise PrebuiltFallback("no compatible Windows CUDA asset was found")

        # AMD ROCm on Windows: try HIP prebuilt
        if host.has_rocm:
            hip_name = f"llama-{llama_tag}-bin-win-hip-radeon-x64.zip"
            if hip_name in upstream_assets:
                log(
                    f"AMD ROCm detected on Windows -- trying upstream HIP prebuilt {hip_name}"
                )
                return AssetChoice(
                    repo = UPSTREAM_REPO,
                    tag = llama_tag,
                    name = hip_name,
                    url = upstream_assets[hip_name],
                    source_label = "upstream",
                    install_kind = "windows-hip",
                )
            log(
                "AMD ROCm detected on Windows but no HIP prebuilt found -- falling back to CPU"
            )

        upstream_name = f"llama-{llama_tag}-bin-win-cpu-x64.zip"
        if upstream_name not in upstream_assets:
            raise PrebuiltFallback("upstream Windows CPU asset was not found")
        return AssetChoice(
            repo = UPSTREAM_REPO,
            tag = llama_tag,
            name = upstream_name,
            url = upstream_assets[upstream_name],
            source_label = "upstream",
            install_kind = "windows-cpu",
        )

    if host.is_macos and host.is_arm64:
        upstream_name = f"llama-{llama_tag}-bin-macos-arm64.tar.gz"
        if upstream_name not in upstream_assets:
            raise PrebuiltFallback("upstream macOS arm64 asset was not found")
        return AssetChoice(
            repo = UPSTREAM_REPO,
            tag = llama_tag,
            name = upstream_name,
            url = upstream_assets[upstream_name],
            source_label = "upstream",
            install_kind = "macos-arm64",
        )

    if host.is_macos and host.is_x86_64:
        upstream_name = f"llama-{llama_tag}-bin-macos-x64.tar.gz"
        if upstream_name not in upstream_assets:
            raise PrebuiltFallback("upstream macOS x64 asset was not found")
        return AssetChoice(
            repo = UPSTREAM_REPO,
            tag = llama_tag,
            name = upstream_name,
            url = upstream_assets[upstream_name],
            source_label = "upstream",
            install_kind = "macos-x64",
        )

    raise PrebuiltFallback(
        f"no prebuilt policy exists for {host.system} {host.machine}"
    )