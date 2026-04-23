def get_guard_fail_reason_helper(
    guard_manager: GuardManagerWrapper,
    f_locals: dict[str, object],
    compile_id: CompileId | None,
    # pyrefly: ignore [implicit-any]
    backend: Callable | None,
) -> str:
    """
    Return the reason why `guard_manager` failed.
    Updates `guard_failures` with the generated reason.
    Only the first failed check of guard_manager is reported.
    """

    assert guard_manager.global_scope is not None
    assert guard_manager.closure_vars is not None
    scope = {"L": f_locals, "G": guard_manager.global_scope["G"]}
    scope.update(guard_manager.closure_vars)
    reasons: list[str] = []

    cache_entry_backend = None
    if guard_manager.cache_entry:
        cache_entry_backend = guard_manager.cache_entry.backend

    no_tensor_aliasing_check_failed = False

    verbose_code_parts: list[str] = []
    guard_debug_info = guard_manager.check_verbose(f_locals)
    user_stack_str = ""

    # For test_export_with_map_cond, the check_verbose fail even without the
    # C++ guard manager. We need to fix the issue to remove the comment.
    # assert not guard_debug_info.result
    if not guard_debug_info.result:
        verbose_code_parts = guard_debug_info.verbose_code_parts
        # verbose_code_parts is either the actual reason (e.g. in case of
        # TENSOR_MATCH) or it could be a list of verbose_code_part that we
        # passed to the leaf guard at construction time. If its a list, we
        # walk through this list and find the guard that failed. This is
        # very important for symbolic shape guards which are currently
        # installed as a lambda guard and can encompass a long list of code_parts.

        if len(verbose_code_parts) == 1:
            if "Duplicate tensor found" in verbose_code_parts[0]:
                no_tensor_aliasing_check_failed = True
            else:
                reasons = verbose_code_parts
                verbose_code_parts = []

        # Format user stack trace if available and recompile logging is enabled
        if guard_debug_info.user_stack:
            user_stack_str = format_user_stack_trace(guard_debug_info.user_stack)
    elif cache_entry_backend != backend:
        # None of the guard entries failed - a backend match issue
        reason = (
            "BACKEND_MATCH failure: torch.compile detected different backend callables."
            " If this is unexpected, wrap your backend in functools.partial (or reuse the"
            " same cached backend) to avoid creating a new backend function each time."
            " More details: https://github.com/pytorch/pytorch/issues/168373"
        )
        reasons.append(reason)
    else:
        # Unexpected recompilation - points to a bug
        reason = (
            "Unexpected recompilation: runtime guards failed even though they passed"
            " during recompilation-reason analysis."
            " Please open an issue with a minimal repro:"
            " https://github.com/pytorch/pytorch"
        )
        reasons.append(reason)

    if no_tensor_aliasing_check_failed:
        reasons = recompilation_reason_for_no_tensor_aliasing_guard(
            guard_manager, scope
        )
    else:
        for part in verbose_code_parts:
            global_scope = dict(guard_manager.global_scope)
            global_scope["__compile_source__"] = part
            with report_compile_source_on_error():
                try:
                    fail_reason = eval(part, global_scope, scope)
                except Exception:
                    if is_recompiles_verbose_enabled():
                        continue
                    else:
                        raise
            # Only ___check_tensors knows how to return a fancy fail reason;
            # for everything else we just report the code that failed

            if isinstance(fail_reason, bool) and not fail_reason:
                fail_reason = part
            if isinstance(fail_reason, str):
                reasons.append(fail_reason)
                if not is_recompiles_verbose_enabled():
                    break

    # Build reason string - simple format for normal logging
    # Use singular "reason" when there's only one, plural "reasons" for multiple
    if len(reasons) == 1:
        reason_str = f"{compile_id}: {reasons[0]}"
    else:
        reason_str = f"{compile_id}: " + "; ".join(reasons)
    if user_stack_str:
        reason_str += f"\nUser stack trace:\n{user_stack_str}"
    return strip_local_scope(reason_str)