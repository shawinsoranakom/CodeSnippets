def resolve_pre_grad_pass_timing() -> Literal["early", "late"]:
    """Resolve the effective pre-grad pass timing from the config.

    "default" is resolved based on whether the custom pass provides a UUID:
    passes with a UUID (or no custom pass) run "late" (after cache lookup),
    passes without a UUID run "early" (before cache lookup).

    Raises RuntimeError if a custom pass without a UUID is explicitly set to
    run "late", since the cache key cannot account for it.
    """
    timing: Literal["early", "late", "default"] = config.pre_grad_pass_timing
    custom_pass = config.pre_grad_custom_pass
    has_uuid = (
        custom_pass
        and isinstance(custom_pass, CustomGraphPass)
        and custom_pass.uuid() is not None
    )

    if timing == "default":
        supports_late = custom_pass is None or has_uuid
        timing = "late" if supports_late else "early"
        if timing == "early" and custom_pass:
            pass_name = type(custom_pass).__qualname__
            if pass_name not in _warned_pre_grad_pass_missing_uuid:
                _warned_pre_grad_pass_missing_uuid.add(pass_name)
                log.warning(
                    "pre_grad_custom_pass %s does not implement uuid(); "
                    "falling back to early timing (pre-grad pass cache will be bypassed). "
                    "Implement uuid() on your CustomGraphPass to enable caching.",
                    pass_name,
                )
                CompileEventLogger.try_add_pt2_compile(
                    "backend_compile",
                    pre_grad_pass_missing_uuid=True,
                    pre_grad_pass_name=pass_name,
                )

    if timing == "late" and custom_pass and not has_uuid:
        raise RuntimeError(
            "pre_grad_custom_pass must implement uuid() to run late "
            "(after cache lookup). Either implement uuid() or set "
            "pre_grad_pass_timing to 'early'."
        )

    return timing