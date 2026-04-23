def log_conversion_errors(
    first_target_key: str,
    loading_info: LoadStateDictInfo | None,
    extras: Any = None,
    op: list[ConversionOps] | ConversionOps | None = None,
):
    """Catch all exceptions during `convert` calls, and log the errors for later. Re-raise a `SkipParameters` exception
    that will be caught later to skip the parameters that raised the original Exception."""
    try:
        yield
    except Exception as e:
        # During reverse mapping, we do not log and skip errors
        if loading_info is None:
            raise e

        def _format_op_name(curr_op: list[ConversionOps] | ConversionOps | None) -> str | None:
            if curr_op is None:
                return None
            if isinstance(curr_op, (list, tuple, set)):
                names = [o.__class__.__name__ for o in curr_op if o is not None]
                if not names:
                    return None
                return ", ".join(names)
            return curr_op.__class__.__name__

        op_name = _format_op_name(op)

        tb_str = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        if isinstance(extras, tuple) and len(extras) == 2:
            length, target_keys = extras
            descriptor = f"{op_name} " if op_name else ""
            loading_info.conversion_errors[first_target_key] = (
                f"{tb_str}{e}\nError: {descriptor}on tensors destined for {target_keys}. Ckpt contains: {length}"
            )
        elif isinstance(extras, str):
            suffix = f" via {op_name}" if op_name else ""
            loading_info.conversion_errors[first_target_key] = (
                f"{tb_str}{e}\nError{suffix} when processing parameter {extras}"
            )
        elif extras is None and op_name:
            loading_info.conversion_errors[first_target_key] = f"{op_name}: {e}"
        else:
            loading_info.conversion_errors[first_target_key] = f"{extras} |Error: {e}"

        # Raise a specific Exception that we can catch easily
        raise SkipParameters()