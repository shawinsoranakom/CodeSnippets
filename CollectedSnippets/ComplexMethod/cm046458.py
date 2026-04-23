def windows_cuda_attempts(
    host: HostInfo,
    llama_tag: str,
    upstream_assets: dict[str, str],
    preferred_runtime_line: str | None,
    selection_preamble: Iterable[str] = (),
) -> list[AssetChoice]:
    selection_log = list(selection_preamble)
    runtime_by_line = {"cuda12": "12.4", "cuda13": "13.1"}
    driver_runtime = pick_windows_cuda_runtime(host)
    detected_runtime_lines, runtime_dirs = detected_windows_runtime_lines()
    compatible_runtime_lines = compatible_windows_runtime_lines(host)
    normal_runtime_lines: list[str]
    if detected_runtime_lines:
        normal_runtime_lines = [
            line for line in compatible_runtime_lines if line in detected_runtime_lines
        ]
    else:
        normal_runtime_lines = compatible_runtime_lines
    selection_log.append(
        "windows_cuda_selection: driver_runtime="
        + (driver_runtime if driver_runtime else "unknown")
    )
    selection_log.append(
        "windows_cuda_selection: detected_runtime_lines="
        + (",".join(detected_runtime_lines) if detected_runtime_lines else "none")
    )
    for runtime_line in ("cuda13", "cuda12"):
        selection_log.append(
            "windows_cuda_selection: runtime_dirs "
            f"{runtime_line}="
            + (
                ",".join(runtime_dirs.get(runtime_line, []))
                if runtime_dirs.get(runtime_line)
                else "none"
            )
        )
    if detected_runtime_lines:
        selection_log.append(
            "windows_cuda_selection: host_runtime_order="
            + (",".join(normal_runtime_lines) if normal_runtime_lines else "none")
        )
    else:
        selection_log.append(
            "windows_cuda_selection: no CUDA runtime DLL line detected; falling back to driver order"
        )
    if not normal_runtime_lines:
        if detected_runtime_lines:
            selection_log.append(
                "windows_cuda_selection: detected CUDA runtime DLLs were incompatible with the reported driver"
            )
        fallback_runtime_lines = (
            ["cuda13", "cuda12"]
            if driver_runtime == "13.1"
            else (["cuda12"] if driver_runtime == "12.4" else [])
        )
        normal_runtime_lines = fallback_runtime_lines

    runtime_order: list[str] = []
    if preferred_runtime_line and preferred_runtime_line in normal_runtime_lines:
        runtime_order.append(preferred_runtime_line)
        selection_log.append(
            "windows_cuda_selection: torch_preferred_runtime_line="
            f"{preferred_runtime_line} reordered_attempts"
        )
    elif preferred_runtime_line:
        selection_log.append(
            "windows_cuda_selection: torch_preferred_runtime_line="
            f"{preferred_runtime_line} unavailable_or_incompatible"
        )
    else:
        selection_log.append(
            "windows_cuda_selection: no Torch runtime preference available"
        )

    runtime_order.extend(
        runtime_line
        for runtime_line in normal_runtime_lines
        if runtime_line not in runtime_order
    )
    selection_log.append(
        "windows_cuda_selection: normal_runtime_order="
        + (",".join(normal_runtime_lines) if normal_runtime_lines else "none")
    )
    selection_log.append(
        "windows_cuda_selection: attempt_runtime_order="
        + (",".join(runtime_order) if runtime_order else "none")
    )

    attempts: list[AssetChoice] = []
    for runtime_line in runtime_order:
        runtime = runtime_by_line[runtime_line]
        selected_name = None
        asset_url = None
        for candidate_name in windows_cuda_upstream_asset_names(llama_tag, runtime):
            asset_url = upstream_assets.get(candidate_name)
            if asset_url:
                selected_name = candidate_name
                break
        if not asset_url or not selected_name:
            selection_log.append(
                "windows_cuda_selection: skip missing assets "
                + ",".join(windows_cuda_upstream_asset_names(llama_tag, runtime))
            )
            continue
        attempts.append(
            AssetChoice(
                repo = UPSTREAM_REPO,
                tag = llama_tag,
                name = selected_name,
                url = asset_url,
                source_label = "upstream",
                install_kind = "windows-cuda",
                runtime_line = runtime_line,
                selection_log = list(selection_log)
                + [
                    f"windows_cuda_selection: selected {selected_name} runtime={runtime}"
                ],
            )
        )
    return attempts