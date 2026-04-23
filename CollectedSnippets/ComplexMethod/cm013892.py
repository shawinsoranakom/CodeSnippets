def lookup_inner(
    obj: Any,
    name: str | None = None,
    filename: str | None = None,
    is_direct_call: bool = True,
    reasons: None | set[str] = None,
) -> type[VariableTracker] | None:
    result = _lookup_inner(
        obj,
        name=name,
        filename=filename,
        is_direct_call=is_direct_call,
        reasons=reasons,
    )
    # There are still some modules we should absolutely NOT trace into - e.g. most of torch._dynamo,
    # as this can result in really weird tracing behaviors.
    # Note that if a torch._dynamo function is already not skipped (e.g. functions in external_utils.py),
    # then this branch does not apply.
    if config.dont_skip_tracing and result is SkipFunctionVariable:
        if filename is None:
            filename = getfile(obj)
        assert filename is not None
        filename = _as_posix_path(filename)
        torch_dir = _module_dir(torch)
        if torch_dir is not None:
            dynamo_path = _as_posix_path(torch_dir) + "_dynamo"
            if filename.startswith(dynamo_path) and not filename.endswith(
                "test_dont_skip_tracing_functions.py"
            ):
                return SkipFunctionVariable
        if reasons is not None:
            reasons.add(
                "Attempted skip but we are ignoring skips due to torch._dynamo.config.dont_skip_tracing"
            )
        return UserFunctionVariable
    return result