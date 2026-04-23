def set_deterministic_debug_mode(debug_mode: builtins.int | str) -> None:
    r"""Sets the debug mode for deterministic operations.

    .. note:: This is an alternative interface for
        :func:`torch.use_deterministic_algorithms`. Refer to that function's
        documentation for details about affected operations.

    Args:
        debug_mode(str or int): If "default" or 0, don't error or warn on
            nondeterministic operations. If "warn" or 1, warn on
            nondeterministic operations. If "error" or 2, error on
            nondeterministic operations.
    """

    # NOTE: builtins.int is used here because int in this scope resolves
    # to torch.int
    if not isinstance(debug_mode, (builtins.int, str)):
        raise TypeError(f"debug_mode must be str or int, but got {type(debug_mode)}")

    if isinstance(debug_mode, str):
        if debug_mode == "default":
            debug_mode = 0
        elif debug_mode == "warn":
            debug_mode = 1
        elif debug_mode == "error":
            debug_mode = 2
        else:
            raise RuntimeError(
                "invalid value of debug_mode, expected one of `default`, "
                f"`warn`, `error`, but got {debug_mode}"
            )

    if debug_mode == 0:
        _C._set_deterministic_algorithms(False)
    elif debug_mode == 1:
        _C._set_deterministic_algorithms(True, warn_only=True)
    elif debug_mode == 2:
        _C._set_deterministic_algorithms(True)
    else:
        raise RuntimeError(
            f"invalid value of debug_mode, expected 0, 1, or 2, but got {debug_mode}"
        )