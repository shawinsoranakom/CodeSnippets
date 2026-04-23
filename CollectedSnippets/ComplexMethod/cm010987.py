def _set_pg_timeout(timeout: timedelta, group: ProcessGroup | None = None) -> None:
    """
    Set the timeout for the given process group when users want to use a different timeout instead of
    default values.

    Args:
        timeout (timedelta): Timeout for operations executed against the process group which
            users want to set. Default value is 10 minutes for NCCL and 30 minutes for other backends.
            This is the duration after which collectives will be aborted asynchronously and the process will crash.
            This is done since CUDA execution is async and it is no longer safe to continue executing user code since
            failed async NCCL operations might result in subsequent CUDA operations running on corrupted data.
            When TORCH_NCCL_BLOCKING_WAIT is set, the process will block and wait for this timeout.

        group (ProcessGroup, optional): The process group to work on. The
            default is the general main process group. If another specific group
            is specified, the calling process must be part of :attr:`group`.

    Returns:
        None
    """
    if group is None:
        group = _get_default_group()
    if _rank_not_in_group(group):
        raise ValueError("Invalid process group specified")
    if not isinstance(group, ProcessGroup):
        raise AssertionError(f"Expected ProcessGroup, got {type(group)}")
    devices = group._device_types
    backends = set()
    if torch.device("cpu") in devices and is_gloo_available():
        backend = group._get_backend(torch.device("cpu"))
        if isinstance(backend, ProcessGroupGloo):
            backends.add(backend)
    if torch.device("cuda") in devices:
        backend = group._get_backend(torch.device("cuda"))
        if is_nccl_available() and isinstance(backend, ProcessGroupNCCL):
            backends.add(backend)  # type: ignore[arg-type]
        elif is_gloo_available() and isinstance(backend, ProcessGroupGloo):
            backends.add(backend)  # type: ignore[arg-type]
        elif _use_torchcomms_enabled() and isinstance(backend, _BackendWrapper):
            backends.add(backend)  # type: ignore[arg-type]
    if len(backends) == 0:
        warnings.warn(
            "Set timeout is now only supported for either nccl or gloo.", stacklevel=2
        )
    for backend in backends:
        backend._set_default_timeout(timeout)