def init_process_group(
    backend: str | None = None,
    init_method: str | None = None,
    timeout: timedelta | None = None,
    world_size: int = -1,
    rank: int = -1,
    store: Store | None = None,
    group_name: str = "",
    pg_options: Any | None = None,
    device_id: torch.device | int | None = None,
    _ranks: list[int] | None = None,
) -> None:
    """
    Initialize the default distributed process group.

    This will also initialize the distributed package.

    There are 2 main ways to initialize a process group:
        1. Specify ``store``, ``rank``, and ``world_size`` explicitly.
        2. Specify ``init_method`` (a URL string) which indicates where/how
           to discover peers. Optionally specify ``rank`` and ``world_size``,
           or encode all required parameters in the URL and omit them.

    If neither is specified, ``init_method`` is assumed to be "env://".


    Args:
        backend (str or Backend, optional): The backend to use. Depending on
            build-time configurations, valid values include ``mpi``, ``gloo``,
            ``nccl``, ``ucc``, ``xccl`` or one that is registered by a third-party
            plugin.
            Since 2.6, if ``backend`` is not provided, c10d will use a backend
            registered for the device type indicated by the `device_id` kwarg
            (if provided). The known default registrations today are: ``nccl``
            for ``cuda``, ``gloo`` for ``cpu``, ``xccl`` for ``xpu``.
            If neither ``backend`` nor ``device_id`` is provided, c10d will
            detect the accelerator on the run-time machine and use a backend
            registered for that detected accelerator (or ``cpu``).
            This field can be given as a lowercase string (e.g., ``"gloo"``),
            which can also be accessed via :class:`Backend` attributes (e.g.,
            ``Backend.GLOO``).
            If using multiple processes per machine with ``nccl`` backend, each
            process must have exclusive access to every GPU it uses, as sharing
            GPUs between processes can result in deadlock or NCCL invalid usage.
            ``ucc`` backend is experimental.
            Default backend for the device can be queried with
            :func:`get_default_backend_for_device`.
        init_method (str, optional): URL specifying how to initialize the
                                     process group. Default is "env://" if no
                                     ``init_method`` or ``store`` is specified.
                                     Mutually exclusive with ``store``.
        world_size (int, optional): Number of processes participating in
                                    the job. Required if ``store`` is specified.
        rank (int, optional): Rank of the current process (it should be a
                              number between 0 and ``world_size``-1).
                              Required if ``store`` is specified.
        store(Store, optional): Key/value store accessible to all workers, used
                                to exchange connection/address information.
                                Mutually exclusive with ``init_method``.
        timeout (timedelta, optional): Timeout for operations executed against
            the process group. Default value is 10 minutes for NCCL and 30 minutes for other backends.
            This is the duration after which collectives will be aborted asynchronously and the process will crash.
            This is done since CUDA execution is async and it is no longer safe to continue executing user code since
            failed async NCCL operations might result in subsequent CUDA operations running on corrupted data.
            When TORCH_NCCL_BLOCKING_WAIT is set, the process will block and wait for this timeout.

        group_name (str, optional, deprecated): Group name. This argument is ignored
        pg_options (ProcessGroupOptions, optional): process group options
            specifying what additional options need to be passed in during
            the construction of specific process groups. As of now, the only
            options we support is ``ProcessGroupNCCL.Options`` for the ``nccl``
            backend, ``is_high_priority_stream`` can be specified so that
            the nccl backend can pick up high priority cuda streams when
            there're compute kernels waiting. For other available options to config nccl,
            See https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/api/types.html#ncclconfig-t
        device_id (torch.device | int, optional): a single, specific device
            this process will work on, allowing for backend-specific
            optimizations.  Currently this has two effects, only under
            NCCL: the communicator is immediately formed (calling
            ``ncclCommInit*`` immediately rather than the normal lazy
            call) and sub-groups will use ``ncclCommSplit`` when
            possible to avoid unnecessary overhead of group creation. If you
            want to know NCCL initialization error early, you can also use this
            field. If an `int` is provided, the API assumes that the accelerator
            type at compile time will be used.
        _ranks: The ranks in the process group. If provided, the process
               group name will be the hash of all the ranks in the group.

    .. note:: To enable ``backend == Backend.MPI``, PyTorch needs to be built from source
        on a system that supports MPI.

    .. note:: Support for multiple backends is experimental. Currently when no backend is
        specified, both ``gloo`` and ``nccl`` backends will be created. The ``gloo`` backend
        will be used for collectives with CPU tensors and the ``nccl`` backend will be used
        for collectives with CUDA tensors. A custom backend can be specified by passing in
        a string with format "<device_type>:<backend_name>,<device_type>:<backend_name>", e.g.
        "cpu:gloo,cuda:custom_backend".

    """

    global _world

    global _backend
    global _default_pg_init_method

    if GroupMember.WORLD is not None:
        raise ValueError("trying to initialize the default process group twice!")

    set_pytorch_distributed_envs_from_justknobs()

    # Depending on the import order, some trace_rules functions may be evaluated
    # during the import phase. In such a case, these functions may not correctly
    # add the distributed related rules due to import circular dependency.
    # We need to clear the lru_cache during the runtime to ensure the correctness
    # of these trace_rules.
    #
    # Since this API must be called before all distributed code being compiled,
    # clearing the cache here should be safe.
    if "torch._dynamo" in sys.modules:
        torch._dynamo.trace_rules.clear_lru_cache()

    if not ((store is None) or (init_method is None)):
        raise AssertionError("Cannot specify both init_method and store.")

    if store is not None:
        if not world_size > 0:
            raise AssertionError("world_size must be positive if using store")
        if not rank >= 0:
            raise AssertionError("rank must be non-negative if using store")
    elif init_method is None:
        init_method = "env://"

    # Get the compile-time accelerator type.
    # None indicates no accelerator support.
    acc = torch.accelerator.current_accelerator()

    # Auto complete device id
    if isinstance(device_id, int):
        if acc is None:
            raise ValueError(
                "device_id is an int, but no accelerator support is found from the current compilation. "
                "Please use a different compiled version that supports your accelerator."
            )
        device_id = torch.device(acc.type, device_id)

    # Sanity check device_id
    if device_id is not None and device_id.type != "cpu":
        # Type
        if acc is None or device_id.type != acc.type:
            raise ValueError(
                f"device_id {device_id} does not match the current compilation's accelerator support: {acc}. "
                "Please use a different compiled version that supports your accelerator."
            )
        # Index
        if device_id.index is None:
            raise ValueError("Please use a device_id with index.")
        # Range
        if device_id.index >= torch.accelerator.device_count():
            raise ValueError(
                f"device_id {device_id} is out of range. Please use a device index less than "
                f"the number of accelerators available: {torch.accelerator.device_count()}."
            )

    logger.info("Using device: %s", device_id)

    # If user did not provide a backend string but provided a device id, e.g.
    # >>> init_process_group(device_id=device)
    # we try to figure out the backend name based on the device type.
    if backend is None and device_id is not None:
        # Note: 3rd-party devices can register default backend through the
        # default map below.
        backend = Backend.default_device_backend_map.get(device_id.type)

    # If we still cannot figure it out, e.g.
    # >>> init_process_group()
    # we set it to `undefined` and rely on lazy init.
    if backend is None:
        backend = "undefined"

    # Convert string into `Backend` type
    backend = Backend(backend)

    if timeout is None:
        timeout = _get_default_timeout(backend)

    _check_valid_timeout(timeout)

    """
    Group name is not visible to users unless they access
    internals of c10d. This means we can ignore the value
    they provide as it not exposed in a public way.
    """
    if _ranks is None or len(_ranks) == 0:
        group_name = _process_group_name([], use_hashed_name=False)
    else:
        group_name = _process_group_name(_ranks, use_hashed_name=True)
    if backend == Backend.MPI:
        if world_size != -1 or rank != -1:
            warnings.warn(
                f"For MPI backend, world_size ({world_size}) and rank ({rank}) "
                "are ignored since they are assigned by the "
                "MPI runtime.",
                stacklevel=2,
            )

        default_pg, _ = _new_process_group_helper(
            -1,
            -1,
            [],
            backend,
            Store(),  # Placeholder value since store cannot be None
            group_name,
            timeout=timeout,
            group_desc="default_pg",
        )
    else:
        # backward compatible API
        if store is None:
            if backend == Backend.FAKE:
                from torch.testing._internal.distributed.fake_pg import FakeStore

                store = FakeStore()
            else:
                rendezvous_iterator = rendezvous(
                    not_none(init_method), rank, world_size, timeout=timeout
                )
                store, rank, world_size = next(rendezvous_iterator)
                store.set_timeout(timeout)

            # Use a PrefixStore to avoid accidental overrides of keys used by
            # different systems (e.g. RPC) in case the store is multi-tenant.
            store = PrefixStore("default_pg", store)

        default_pg, _ = _new_process_group_helper(
            world_size,
            rank,
            [],
            backend,
            store,
            group_name,
            backend_options=pg_options,
            timeout=timeout,
            device_id=device_id,
            group_desc="default_pg",
        )

    _update_default_pg(default_pg)

    _world.pg_group_ranks[GroupMember.WORLD] = {  # type: ignore[index]
        i: i
        for i in range(GroupMember.WORLD.size())  # type: ignore[attr-defined]
    }
    _backend = _world.pg_map[not_none(GroupMember.WORLD)][0]
    _default_pg_init_method = init_method

    old_hook = sys.excepthook
    excepthook_prefix = f"[rank{get_rank()}]"

    def _distributed_excepthook(*args):
        old_stderr = sys.stderr
        sys.stderr = buf = io.StringIO()
        try:
            old_hook(*args)
        finally:
            sys.stderr = old_stderr
        msg = buf.getvalue()
        msg = "\n".join(
            f"{excepthook_prefix}: {s}" if s != "" else "" for s in msg.split("\n")
        )
        sys.stderr.write(msg)
        sys.stderr.flush()

    sys.excepthook = _distributed_excepthook

    if _is_barrier_after_init() == 1:
        # barrier at the end to ensure that once we return from this method, all
        # process groups including global variables (if any) are updated
        # correctly on all ranks.
        # Update 04/2023: for large-scale runs, this barrier (esp. store-based
        # barrier) may be costly and/or unscalable. Also, in a lot of cases,
        # these barriers may be unnecessary, as proven by a green CI after
        # removal. An environment variable `TORCH_DIST_INIT_BARRIER` has been
        # added which enables this barrier only when set to 1.
        logger.debug(
            "Performing barrier after ProcessGroup initialization since "
            "TORCH_DIST_INIT_BARRIER = 1"
        )
        if backend == Backend.MPI:
            # MPI backend doesn't use store.
            barrier()
        else:
            # Use store based barrier here since barrier() used a bunch of
            # default devices and messes up NCCL internal state.
            _store_based_barrier(rank, store, group_name, world_size, timeout)