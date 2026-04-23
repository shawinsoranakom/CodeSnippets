def validate_prebuilt_attempts(
    attempts: Iterable[AssetChoice],
    host: HostInfo,
    install_dir: Path,
    work_dir: Path,
    probe_path: Path,
    *,
    requested_tag: str,
    llama_tag: str,
    release_tag: str,
    approved_checksums: ApprovedReleaseChecksums,
    initial_fallback_used: bool = False,
    existing_install_dir: Path | None = None,
) -> tuple[AssetChoice, Path, bool]:
    attempt_list = list(attempts)
    if not attempt_list:
        raise PrebuiltFallback("no prebuilt bundle attempts were available")

    tried_fallback = initial_fallback_used
    for index, attempt in enumerate(attempt_list):
        if index > 0:
            tried_fallback = True
            log(
                "retrying CUDA prebuilt "
                f"{attempt.name} install_kind={attempt.install_kind} "
                f"runtime_line={attempt.runtime_line} coverage_class={attempt.coverage_class}"
            )

        if existing_install_dir is not None and existing_install_matches_choice(
            existing_install_dir,
            host,
            llama_tag = llama_tag,
            release_tag = release_tag,
            choice = attempt,
            approved_checksums = approved_checksums,
        ):
            log(
                "existing llama.cpp install already matches fallback candidate "
                f"{attempt.name}; skipping reinstall"
            )
            raise ExistingInstallSatisfied(attempt, tried_fallback)

        staging_dir = create_install_staging_dir(install_dir)
        quantized_path = work_dir / f"stories260K-q4-{index}.gguf"
        if quantized_path.exists():
            quantized_path.unlink()
        try:
            validate_prebuilt_choice(
                attempt,
                host,
                staging_dir,
                work_dir,
                probe_path,
                requested_tag = requested_tag,
                llama_tag = llama_tag,
                release_tag = release_tag,
                approved_checksums = approved_checksums,
                prebuilt_fallback_used = tried_fallback,
                quantized_path = quantized_path,
            )
        except Exception as exc:
            remove_tree(staging_dir)
            prune_install_staging_root(install_dir)
            if isinstance(exc, PrebuiltFallback):
                attempt_error = exc
            else:
                attempt_error = PrebuiltFallback(
                    f"candidate attempt failed before activation for {attempt.name}: {exc}"
                )
            if index == len(attempt_list) - 1:
                raise attempt_error from exc
            log(
                "selected CUDA bundle failed before activation; trying next prebuilt fallback "
                f"({textwrap.shorten(str(attempt_error), width = 200, placeholder = '...')})"
            )
            continue

        return attempt, staging_dir, tried_fallback

    raise PrebuiltFallback("no prebuilt bundle passed validation")