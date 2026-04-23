def augment_exc_message(exc: Exception, msg: str = "\n", export: bool = False) -> None:
    import traceback

    exc.innermost_user_frame_summary = None  # type: ignore[attr-defined]

    real_stack = get_real_stack(exc)
    if real_stack is not None and len(real_stack) > 0:
        exc.innermost_user_frame_summary = real_stack[-1]  # type: ignore[attr-defined]
        msg += f"\nfrom user code:\n {''.join(traceback.format_list(real_stack))}"

    if config.replay_record_enabled and hasattr(exc, "record_filename"):
        msg += (
            f"\nLast frame execution written to {exc.record_filename}. To run only this frame while debugging, run\
 torch._dynamo.replay('{exc.record_filename}').\n"
        )

    if not config.verbose and hasattr(exc, "real_stack"):
        msg += (
            "\nSet TORCHDYNAMO_VERBOSE=1 for the internal stack trace "
            "(please do this especially if you're reporting a bug to PyTorch). "
            'For even more developer context, set TORCH_LOGS="+dynamo"\n'
        )

    if hasattr(exc, "inner_exception") and hasattr(
        exc.inner_exception, "minifier_path"
    ):
        if hasattr(exc.inner_exception, "buck_command"):
            msg += (
                f"\nMinifier script written to {exc.inner_exception.minifier_path}. Run "
                f"this buck command to find the smallest traced graph "
                f"which reproduces this error: {exc.inner_exception.buck_command}\n"
            )
        else:
            msg += (
                f"\nMinifier script written to {exc.inner_exception.minifier_path}. Run "
                "this script to find the smallest traced graph which reproduces this error.\n"
            )

    old_msg = "" if len(exc.args) == 0 else str(exc.args[0])

    old_msg = augment_exc_message_with_hop_name(exc, old_msg)

    if isinstance(exc, KeyError):
        exc.args = (KeyErrorMsg(old_msg + msg),) + exc.args[1:]
    else:
        new_msg = old_msg + msg
        exc.args = (new_msg,) + exc.args[1:]