def resolve_simple_install_release_plans(
    llama_tag: str,
    host: HostInfo,
    published_repo: str,
    published_release_tag: str,
    *,
    max_release_fallbacks: int = DEFAULT_MAX_PREBUILT_RELEASE_FALLBACKS,
) -> tuple[str, list[InstallReleasePlan]]:
    repo = published_repo or DEFAULT_PUBLISHED_REPO
    requested_tag = normalized_requested_llama_tag(llama_tag)
    allow_older_release_fallback = (
        requested_tag == "latest" and not published_release_tag
    )
    release_limit = max(1, max_release_fallbacks)
    plans: list[InstallReleasePlan] = []
    last_error: PrebuiltFallback | None = None

    try:
        releases = iter_release_payloads_by_time(
            repo, published_release_tag, requested_tag
        )
        for release in releases:
            try:
                if host.is_linux and repo == "unslothai/llama.cpp":
                    plan = direct_linux_release_plan(release, host, repo, requested_tag)
                else:
                    plan = direct_upstream_release_plan(
                        release, host, repo, requested_tag
                    )
                if plan is None:
                    continue
            except PrebuiltFallback as exc:
                last_error = exc
                if not allow_older_release_fallback:
                    raise
                release_tag = release.get("tag_name") or "unknown"
                log(
                    "published release skipped for install planning: "
                    f"{repo}@{release_tag} ({exc})"
                )
                continue

            plans.append(plan)
            if not allow_older_release_fallback or len(plans) >= release_limit:
                break
    except PrebuiltFallback:
        raise
    except Exception as exc:
        raise PrebuiltFallback(
            f"failed to inspect published releases in {repo}: {exc}"
        ) from exc

    if plans:
        return requested_tag, plans
    if last_error is not None:
        raise last_error
    raise PrebuiltFallback(
        f"no installable published llama.cpp releases were found in {repo}"
    )