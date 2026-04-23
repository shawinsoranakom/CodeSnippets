def linux_cuda_choice_from_release(
    host: HostInfo,
    release: PublishedReleaseBundle,
    preferred_runtime_line: str | None = None,
    selection_preamble: Iterable[str] = (),
) -> LinuxCudaSelection | None:
    host_sms = normalize_compute_caps(host.compute_caps)
    detected_runtime_lines, runtime_dirs = detected_linux_runtime_lines()
    driver_runtime_lines = compatible_linux_runtime_lines(host)
    runtime_lines = [
        runtime_line
        for runtime_line in detected_runtime_lines
        if runtime_line in driver_runtime_lines
    ]
    ordered_runtime_lines = list(runtime_lines)
    selection_log = (
        list(release.selection_log)
        + list(selection_preamble)
        + [
            f"linux_cuda_selection: release={release.release_tag}",
            f"linux_cuda_selection: detected_sms={','.join(host_sms) if host_sms else 'unknown'}",
            "linux_cuda_selection: detected_runtime_lines="
            + (",".join(detected_runtime_lines) if detected_runtime_lines else "none"),
            "linux_cuda_selection: driver_runtime_lines="
            + (",".join(driver_runtime_lines) if driver_runtime_lines else "none"),
            "linux_cuda_selection: compatible_runtime_lines="
            + (",".join(runtime_lines) if runtime_lines else "none"),
        ]
    )
    for runtime_line in ("cuda13", "cuda12"):
        selection_log.append(
            "linux_cuda_selection: runtime_dirs "
            f"{runtime_line}="
            + (
                ",".join(runtime_dirs.get(runtime_line, []))
                if runtime_dirs.get(runtime_line)
                else "none"
            )
        )
    published_artifacts = [
        artifact
        for artifact in release.artifacts
        if artifact.install_kind == "linux-cuda"
    ]
    published_asset_names = sorted(
        artifact.asset_name for artifact in published_artifacts
    )
    selection_log.append(
        "linux_cuda_selection: published_assets="
        + (",".join(published_asset_names) if published_asset_names else "none")
    )

    if not host_sms:
        selection_log.append(
            "linux_cuda_selection: compute capability detection unavailable; prefer portable by runtime line"
        )
    if not runtime_lines:
        selection_log.append(
            "linux_cuda_selection: no Linux CUDA runtime line satisfied both runtime libraries and driver compatibility"
        )
        return None

    if preferred_runtime_line:
        if preferred_runtime_line in ordered_runtime_lines:
            ordered_runtime_lines = [preferred_runtime_line] + [
                runtime_line
                for runtime_line in ordered_runtime_lines
                if runtime_line != preferred_runtime_line
            ]
            selection_log.append(
                "linux_cuda_selection: torch_preferred_runtime_line="
                f"{preferred_runtime_line} reordered_attempts={','.join(ordered_runtime_lines)}"
            )
        else:
            selection_log.append(
                "linux_cuda_selection: torch_preferred_runtime_line="
                f"{preferred_runtime_line} unavailable_on_host"
            )

    attempts: list[AssetChoice] = []
    seen_attempts: set[str] = set()

    def add_attempt(
        artifact: PublishedLlamaArtifact, asset_url: str, reason: str
    ) -> None:
        asset_name = artifact.asset_name
        if asset_name in seen_attempts:
            return
        seen_attempts.add(asset_name)
        attempts.append(
            AssetChoice(
                repo = release.repo,
                tag = release.release_tag,
                name = asset_name,
                url = asset_url,
                source_label = "published",
                is_ready_bundle = True,
                install_kind = "linux-cuda",
                bundle_profile = artifact.bundle_profile,
                runtime_line = artifact.runtime_line,
                coverage_class = artifact.coverage_class,
                supported_sms = artifact.supported_sms,
                min_sm = artifact.min_sm,
                max_sm = artifact.max_sm,
                selection_log = list(selection_log)
                + [
                    "linux_cuda_selection: selected "
                    f"{asset_name} runtime_line={artifact.runtime_line} coverage_class={artifact.coverage_class} reason={reason}"
                ],
            )
        )

    for runtime_line in ordered_runtime_lines:
        coverage_candidates: list[tuple[PublishedLlamaArtifact, str]] = []
        portable_candidate: tuple[PublishedLlamaArtifact, str] | None = None
        for artifact in published_artifacts:
            if artifact.runtime_line != runtime_line:
                continue
            asset_name = artifact.asset_name
            asset_url = release.assets.get(asset_name)
            if not asset_url:
                selection_log.append(
                    f"linux_cuda_selection: reject {asset_name} missing asset"
                )
                continue
            if not host_sms and artifact.coverage_class != "portable":
                selection_log.append(
                    "linux_cuda_selection: reject "
                    f"{asset_name} runtime_line={runtime_line} coverage_class={artifact.coverage_class} "
                    "reason=unknown_compute_caps_prefer_portable"
                )
                continue

            if not artifact.supported_sms:
                selection_log.append(
                    "linux_cuda_selection: reject "
                    f"{asset_name} runtime_line={runtime_line} coverage_class={artifact.coverage_class} "
                    "reason=artifact_missing_supported_sms"
                )
                continue
            if artifact.min_sm is None or artifact.max_sm is None:
                selection_log.append(
                    "linux_cuda_selection: reject "
                    f"{asset_name} runtime_line={runtime_line} coverage_class={artifact.coverage_class} "
                    "reason=artifact_missing_sm_bounds"
                )
                continue

            supported_sms = {str(value) for value in artifact.supported_sms}
            missing_sms = [sm for sm in host_sms if sm not in supported_sms]
            out_of_range_sms = [
                sm
                for sm in host_sms
                if not (artifact.min_sm <= int(sm) <= artifact.max_sm)
            ]
            reasons: list[str] = []
            if missing_sms:
                reasons.append(f"missing_sms={','.join(missing_sms)}")
            if out_of_range_sms:
                reasons.append(f"out_of_range_sms={','.join(out_of_range_sms)}")
            if reasons:
                selection_log.append(
                    "linux_cuda_selection: reject "
                    f"{asset_name} runtime_line={runtime_line} coverage_class={artifact.coverage_class} "
                    f"coverage={artifact.min_sm}-{artifact.max_sm} supported={','.join(artifact.supported_sms)} "
                    f"reasons={' '.join(reasons)}"
                )
                continue

            selection_log.append(
                "linux_cuda_selection: accept "
                f"{asset_name} runtime_line={runtime_line} coverage_class={artifact.coverage_class} "
                f"coverage={artifact.min_sm}-{artifact.max_sm} supported={','.join(artifact.supported_sms)}"
            )
            if artifact.coverage_class == "portable":
                portable_candidate = (artifact, asset_url)
            else:
                coverage_candidates.append((artifact, asset_url))

        if coverage_candidates:
            artifact, url = sorted(
                coverage_candidates,
                key = lambda item: (
                    (item[0].max_sm or 0) - (item[0].min_sm or 0),
                    item[0].rank,
                    item[0].max_sm or 0,
                ),
            )[0]
            add_attempt(artifact, url, "best coverage for runtime line")
        if portable_candidate:
            artifact, url = portable_candidate
            add_attempt(artifact, url, "portable fallback for runtime line")

    if not attempts:
        return None

    selection_log.append(
        "linux_cuda_selection: attempt_order="
        + ",".join(choice.name for choice in attempts)
    )
    for attempt in attempts:
        attempt.selection_log = list(selection_log) + [
            "linux_cuda_selection: attempt "
            f"{attempt.name} runtime_line={attempt.runtime_line} coverage_class={attempt.coverage_class}"
        ]
    return LinuxCudaSelection(attempts = attempts, selection_log = selection_log)