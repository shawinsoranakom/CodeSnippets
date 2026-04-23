def published_windows_cuda_attempts(
    host: HostInfo,
    release: PublishedReleaseBundle,
    preferred_runtime_line: str | None,
    selection_preamble: Iterable[str] = (),
) -> list[AssetChoice]:
    selection_log = list(release.selection_log) + list(selection_preamble)
    runtime_by_line = {"cuda12": "12.4", "cuda13": "13.1"}
    runtime_order = windows_cuda_attempts(
        host,
        release.upstream_tag,
        {
            f"llama-{release.upstream_tag}-bin-win-cuda-{runtime}-x64.zip": "published"
            for runtime in runtime_by_line.values()
        },
        preferred_runtime_line,
        selection_log,
    )
    published_artifacts = [
        artifact
        for artifact in release.artifacts
        if artifact.install_kind == "windows-cuda"
    ]
    artifacts_by_runtime: dict[str, list[PublishedLlamaArtifact]] = {}
    for artifact in published_artifacts:
        if not artifact.runtime_line:
            continue
        artifacts_by_runtime.setdefault(artifact.runtime_line, []).append(artifact)

    attempts: list[AssetChoice] = []
    for ordered_attempt in runtime_order:
        runtime_line = ordered_attempt.runtime_line
        if not runtime_line:
            continue
        candidates = sorted(
            artifacts_by_runtime.get(runtime_line, []),
            key = lambda artifact: (artifact.rank, artifact.asset_name),
        )
        for artifact in candidates:
            asset_url = release.assets.get(artifact.asset_name)
            if not asset_url:
                continue
            attempts.append(
                AssetChoice(
                    repo = release.repo,
                    tag = release.release_tag,
                    name = artifact.asset_name,
                    url = asset_url,
                    source_label = "published",
                    install_kind = "windows-cuda",
                    runtime_line = runtime_line,
                    selection_log = list(ordered_attempt.selection_log or [])
                    + [
                        "windows_cuda_selection: selected published asset "
                        f"{artifact.asset_name} for runtime_line={runtime_line}"
                    ],
                )
            )
            break
    return attempts