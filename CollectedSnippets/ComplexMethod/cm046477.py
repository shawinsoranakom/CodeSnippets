def resolve_install_release_plans(
    llama_tag: str,
    host: HostInfo,
    published_repo: str,
    published_release_tag: str,
    *,
    max_release_fallbacks: int = DEFAULT_MAX_PREBUILT_RELEASE_FALLBACKS,
) -> tuple[str, list[InstallReleasePlan]]:
    requested_tag = normalized_requested_llama_tag(llama_tag)
    allow_older_release_fallback = (
        requested_tag == "latest" and not published_release_tag
    )
    release_limit = max(1, max_release_fallbacks)
    plans: list[InstallReleasePlan] = []
    last_error: PrebuiltFallback | None = None

    for resolved_release in iter_resolved_published_releases(
        llama_tag,
        published_repo,
        published_release_tag,
    ):
        bundle = resolved_release.bundle
        checksums = resolved_release.checksums
        resolved_tag = bundle.upstream_tag
        try:
            if host.is_linux and host.is_x86_64 and host.has_usable_nvidia:
                linux_cuda_selection = resolve_linux_cuda_choice(host, bundle)
                attempts = apply_approved_hashes(
                    linux_cuda_selection.attempts, checksums
                )
                if not attempts:
                    raise PrebuiltFallback("no compatible Linux CUDA asset was found")
                log_lines(linux_cuda_selection.selection_log)
            else:
                attempts = resolve_release_asset_choice(
                    host,
                    resolved_tag,
                    bundle,
                    checksums,
                )
                if not attempts:
                    raise PrebuiltFallback("no compatible prebuilt asset was found")
                if attempts[0].selection_log:
                    log_lines(attempts[0].selection_log)
        except PrebuiltFallback as exc:
            last_error = exc
            if not allow_older_release_fallback:
                raise
            log(
                "published release skipped for install planning: "
                f"{bundle.repo}@{bundle.release_tag} upstream_tag={resolved_tag} ({exc})"
            )
            continue

        plans.append(
            InstallReleasePlan(
                requested_tag = requested_tag,
                llama_tag = resolved_tag,
                release_tag = bundle.release_tag,
                attempts = attempts,
                approved_checksums = checksums,
            )
        )

        if not allow_older_release_fallback or len(plans) >= release_limit:
            break

    if plans:
        return requested_tag, plans
    if last_error is not None:
        raise last_error
    raise PrebuiltFallback("no installable published llama.cpp releases were found")