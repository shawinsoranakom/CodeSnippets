def install_prebuilt(
    install_dir: Path,
    llama_tag: str,
    published_repo: str,
    published_release_tag: str,
    *,
    simple_policy: bool = False,
) -> None:
    host = detect_host()
    choice: AssetChoice | None = None
    try:
        with install_lock(install_lock_path(install_dir)):
            if install_dir.exists():
                log(
                    f"existing llama.cpp install detected at {install_dir}; validating staged prebuilt update before replacement"
                )
            else:
                log(
                    f"no existing llama.cpp install detected at {install_dir}; performing fresh prebuilt install"
                )
            if simple_policy:
                requested_tag, release_plans = resolve_simple_install_release_plans(
                    llama_tag,
                    host,
                    published_repo,
                    published_release_tag,
                )
            else:
                requested_tag, release_plans = resolve_install_release_plans(
                    llama_tag,
                    host,
                    published_repo,
                    published_release_tag,
                )
            if release_plans and existing_install_matches_plan(
                install_dir, host, release_plans[0]
            ):
                current = release_plans[0]
                log(
                    "existing llama.cpp install already matches selected release "
                    f"{current.release_tag} upstream_tag={current.llama_tag}; skipping download and install"
                )
                return
            with tempfile.TemporaryDirectory(prefix = "unsloth-llama-prebuilt-") as tmp:
                work_dir = Path(tmp)
                probe_path = work_dir / "stories260K.gguf"
                download_validation_model(
                    probe_path, validation_model_cache_path(install_dir)
                )
                release_count = len(release_plans)
                for release_index, plan in enumerate(release_plans):
                    choice = plan.attempts[0]
                    if existing_install_matches_plan(install_dir, host, plan):
                        log(
                            "existing llama.cpp install already matches fallback release "
                            f"{plan.release_tag} upstream_tag={plan.llama_tag}; skipping reinstall"
                        )
                        return
                    log(
                        "selected "
                        f"{choice.name} ({choice.source_label}) from published release "
                        f"{plan.release_tag} for {host.system} {host.machine}"
                    )
                    try:
                        choice, selected_staging_dir, _ = validate_prebuilt_attempts(
                            plan.attempts,
                            host,
                            install_dir,
                            work_dir,
                            probe_path,
                            requested_tag = requested_tag,
                            llama_tag = plan.llama_tag,
                            release_tag = plan.release_tag,
                            approved_checksums = plan.approved_checksums,
                            initial_fallback_used = release_index > 0,
                            existing_install_dir = install_dir,
                        )
                    except ExistingInstallSatisfied:
                        return
                    except PrebuiltFallback as exc:
                        if release_index == release_count - 1:
                            raise
                        log(
                            "published release "
                            f"{plan.release_tag} upstream_tag={plan.llama_tag} failed; "
                            "trying the next older published prebuilt "
                            f"({textwrap.shorten(str(exc), width = 200, placeholder = '...')})"
                        )
                        continue

                    activate_install_tree(selected_staging_dir, install_dir, host)
                    try:
                        ensure_converter_scripts(install_dir, plan.llama_tag)
                    except Exception as exc:
                        log(
                            "converter script fetch failed after activation; install remains valid "
                            f"({textwrap.shorten(str(exc), width = 200, placeholder = '...')})"
                        )
                    return
    except BusyInstallConflict as exc:
        log("prebuilt install path is blocked by an in-use llama.cpp install")
        log(f"prebuilt busy reason: {exc}")
        raise SystemExit(EXIT_BUSY) from exc
    except PrebuiltFallback as exc:
        log("prebuilt install path failed; falling back to source build")
        log(f"prebuilt fallback reason: {exc}")
        report = collect_system_report(host, choice, install_dir)
        print(report)
        raise SystemExit(EXIT_FALLBACK) from exc