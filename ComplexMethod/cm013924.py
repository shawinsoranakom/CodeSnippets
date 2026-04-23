def get_and_maybe_log_recompilation_reasons(
    cache_entry: CacheEntry | None,
    frame: DynamoFrameType,
    # pyrefly: ignore [implicit-any]
    backend: Callable,
    skip_logging: bool = False,
) -> list[str]:
    """
    Return the list of guard failure reasons using cache_entry.
    Logs the recompilation reason if `recompiles` logging is enabled.
    Raises a RecompileError if `config.error_on_recompile` is enabled.
    """
    # pyrefly: ignore [implicit-any]
    reasons = []
    while cache_entry is not None:
        reason = get_guard_fail_reason(
            cache_entry.guard_manager,
            cache_entry.code,
            frame.f_locals,
            cache_entry.compile_id,
            backend,
            skip_logging,
        )
        if reason:
            reasons.append(reason)
        cache_entry = cache_entry.next

    code = frame.f_code

    if skip_logging:
        return reasons
    # at least one of "recompiles" or "recompiles_verbose" is enabled
    do_recompiles_log = is_recompiles_enabled() or is_recompiles_verbose_enabled()

    if do_recompiles_log or config.error_on_recompile:
        if is_recompiles_verbose_enabled():
            failures = "\n\n".join(
                f"guard {i} failures:\n" + textwrap.indent(reason, "- ")
                for i, reason in enumerate(reasons)
            )
        else:
            failures = textwrap.indent("\n".join(reasons), "- ")
        guard_failure_details = (
            f"triggered by the following guard failure(s):\n{failures}"
        )
        message = (
            f"Recompiling function {code.co_name} in {code.co_filename}:{code.co_firstlineno}\n"
            f"{textwrap.indent(guard_failure_details, '    ')}"
        )
        if do_recompiles_log:
            if is_recompiles_verbose_enabled():
                recompiles_verbose_log.debug(message)
            else:
                recompiles_log.debug(message)
        if config.error_on_recompile:
            raise exc.RecompileError(message)

    torch._logging.trace_structured(
        "artifact",
        metadata_fn=lambda: {
            "name": "recompile_reasons",
            "encoding": "json",
        },
        payload_fn=lambda: reasons[0] if len(reasons) == 1 else reasons,
    )

    return reasons