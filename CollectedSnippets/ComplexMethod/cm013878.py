def check_inlineable(
        func: BaseUserFunctionVariable,
    ) -> trace_rules.SkipResult:
        if func.has_self():
            unimplemented(
                gb_type="Inline attempt with __self__",
                context=str(func),
                explanation="Attempted to inline a function with the `__self__` attribute. "
                "Dynamo is expected to decompose method calls into function calls with a `self` argument.",
                hints=[],
            )

        if isinstance(func, UserFunctionVariable) and inspect.getattr_static(
            func.get_function(), "_torchdynamo_disable", False
        ):
            msg = inspect.getattr_static(
                func.get_function(), "_torchdynamo_disable_msg", None
            )
            unimplemented(
                gb_type="Skip inlining `torch.compiler.disable()`d function",
                context=str(func.get_function()),
                explanation=f"Skip inlining function {func.get_function()} since it was wrapped "
                f"with `torch.compiler.disable` (reason: {msg})",
                hints=[
                    "Remove the `torch.compiler.disable` call",
                ],
            )

        result = trace_rules.check_verbose(func, is_inlined_call=True)
        if result.skipped:
            from torch._dynamo.variables.misc import produce_trampoline_autograd_apply

            # _origin marks this as coming from an internal dynamo known function that is safe to
            # trace through.
            if (
                hasattr(func, "fn")
                and hasattr(func.fn, "_origin")
                and func.fn._origin is produce_trampoline_autograd_apply
            ):
                # Known sound
                return trace_rules.SkipResult(
                    False, "allowlist in dynamo known function"
                )
            fn_qualname = func.fn.__qualname__ if hasattr(func, "fn") else ""
            hints = [
                f"Avoid calling the function `{fn_qualname}`.",
            ]
            if "_dynamo" not in func.get_filename():
                hints += [
                    f"Apply `@torch._dynamo.dont_skip_tracing` to the function `{fn_qualname}` "
                    "to force tracing into the function. "
                    "More graph breaks may occur as a result of attempting to trace into the function.",
                    "Please file an issue to PyTorch.",
                ]
            unimplemented(
                gb_type="Attempted to inline function marked as skipped",
                context=f"qualname: {fn_qualname}, name: {func.get_name()}, "
                f"filename: `{func.get_filename()}`, skip reason: {result.reason}",
                explanation=f"Dynamo developers have intentionally marked that the function `{fn_qualname}` "
                "should not be traced.",
                hints=hints,
            )

        return result