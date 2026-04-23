def _callback_from_stance(callback: DynamoCallback) -> DynamoCallback:
    if _stance.stance == "default":
        # force_backend
        if _stance.backend is not None and callback not in (False, None):
            callback = _create_wrapped_callback(get_compiler_fn(_stance.backend))

        return callback
    elif _stance.stance == "eager_then_compile":
        if callback not in (False, None):
            return _create_delayed_compile_callback(callback, _stance.stance)
        return callback
    elif _stance.stance == "aot_eager_then_compile":
        if callback not in (False, None):
            return _create_delayed_compile_callback(callback, _stance.stance)
        return callback
    elif _stance.stance == "force_eager":
        # disable
        return None
    elif _stance.stance == "eager_on_recompile":
        # run mode
        return False
    elif _stance.stance == "fail_on_recompile":
        if callback in (False, None):
            return callback

        def fail_callback(
            frame: DynamoFrameType, *args: Any, **kwargs: Any
        ) -> ConvertFrameReturn:
            if trace_rules.check(frame.f_code):
                return ConvertFrameReturn()
            if not convert_frame.has_tensor_in_frame(frame):
                return ConvertFrameReturn()

            from torch._C._dynamo.eval_frame import (
                _debug_get_cache_entry_list,
                _debug_get_precompile_entries,
            )
            from torch._dynamo.guards import get_and_maybe_log_recompilation_reasons

            message = (
                "Detected recompile when torch.compile stance is 'fail_on_recompile'. "
                + f"filename: '{frame.f_code.co_filename}', "
                + f"function name: '{frame.f_code.co_name}', "
                + f"line number: {frame.f_lineno}"
            )
            cache_entries = _debug_get_cache_entry_list(frame.f_code)
            if cache_entries:
                reasons = get_and_maybe_log_recompilation_reasons(
                    # pyrefly: ignore [bad-argument-type]
                    cache_entries[0],
                    frame,
                    # pyrefly: ignore [bad-argument-type]
                    innermost_fn(callback),
                    skip_logging=True,
                )
                if reasons:
                    failures = textwrap.indent("\n".join(reasons), "- ")
                    guard_failure_details = (
                        f"triggered by the following guard failure(s):\n{failures}"
                    )
                    message += f"\n{textwrap.indent(guard_failure_details, '    ')}"
            precompile_entries = _debug_get_precompile_entries(frame.f_code)
            if len(precompile_entries) > 0:
                message += "\nFailed on the following precompiled guards: "
                for entry in precompile_entries:
                    message += f"\n{entry.guard_manager}{entry.guard_manager.check_verbose(frame.f_locals)}"  # type: ignore[attr-defined]
            raise RuntimeError(message)

        # to prevent cache miss due to different backend
        fail_callback._torchdynamo_orig_backend = callback  # type: ignore[attr-defined]

        return fail_callback
    else:
        raise RuntimeError(f"invalid torch.compile stance '{_stance}'")