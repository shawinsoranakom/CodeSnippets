def load(
    state_dict: dict[str, Any],
    *,
    checkpoint_id: str | os.PathLike | None = None,
    storage_reader: StorageReader | None = None,
    planner: LoadPlanner | None = None,
    process_group: dist.ProcessGroup | None = None,
    no_dist: bool = False,
) -> None:
    """
    Load a checkpoint into a distributed state dict in SPMD style.

    Each rank must have the same keys in their ``state_dict`` provided to this
    API. Mismatched keys may result in hangs or errors. If unsure, you can use
    the ``utils._assert_same_keys`` API to check (but may incur communication
    costs).

    Each rank will try to read the least amount of data necessary
    to fulfill the requested `state_dict`. When loading :class:`ShardedTensor`
    or :class:`DTensor` instances, each rank only reads data for their local shards.

    For each ``Stateful`` object (having both a ``state_dict`` and a ``load_state_dict``),
    load will first call ``state_dict`` before attempting deserialization, followed by
    ``load_state_dict`` once the deserialization is complete.
    For each non-``Stateful`` object, load will deserialize the object, and then replace
    it in the ``state_dict`` with the deserialized object.

    .. warning::
        All tensors in ``state_dict`` must be allocated on their
        destination device *prior to* calling this function.

        All non-tensor data is loaded using `torch.load()` and modified in place
        on state_dict.

    .. warning::
        Users must call `load_state_dict` on the root module to ensure load
        pos-processing and non-tensor data properly propagates.

    .. note:
        If no process group is initialized, this function will assume the intent
        is to load a checkpoint into the local process. This can be useful in the
        case of local inference, and when using regular Tensors (as opposed to DTensor
         or ShardedTensor)

    .. note:
        Rank 0 is assumed to be the coordinator rank.

    Args:
        state_dict (Dict[str, Any]): The state_dict to load the checkpoint into.
        checkpoint_id (Union[str, os.PathLike, None]):
            The ID of this checkpoint instance. The meaning of the checkpoint_id
            depends on the storage. It can be a path to a folder or to a file.
            It can also be a key if the storage is a key-value store.
            (Default: ``None``)
        storage_reader (Optional[StorageReader]):
            Instance of StorageWriter used to perform reads. If this is not
            specified, DCP will automatically infer the reader based on the
            checkpoint_id. If checkpoint_id is also None, an exception will
            be raised. (Default: ``None``)
        planner (Optional[LoadPlanner]):
            Instance of LoadPlanner. If this is not specified, the default
            planner will be used. (Default: ``None``)
        process_group (Optional[ProcessGroup]):
            ProcessGroup to be used for cross-rank synchronization.
            (Default: ``None``)
        no_dist (bool): If ``True``, this function will assume the intent is to load
            a checkpoint without using cross-rank synchronization. (Default: ``False``)
    Returns:
        None.

    Examples
        >>> # xdoctest: +SKIP
        >>> my_model = MyModule()
        >>> optimizer = Adagrad(my_model.parameters())
        >>> model_state_dict = my_model.state_dict()
        >>> fs_storage_reader = torch.distributed.checkpoint.FileSystemReader(
        ...     "/checkpoint/1"
        ... )

        >>> torch.distributed.checkpoint.load_state_dict(
        >>>     state_dict=model_state_dict,
        >>>     storage_reader=fs_storage_reader,
        >>> )

        >>> # module.load_state_dict() function might have customized steps
        >>> # to flush the state_dict, must call it to
        >>> # ensure correct behavior.
        >>> my_model.load_state_dict(model_state_dict)

    .. note::
        load_state_dict uses collectives to coordinate reads across ranks.
        For NCCL-based process groups, internal tensor representations of
        objects must be moved to the GPU device before communication takes place.
        In this case, the device used is given by ``torch.cuda.current_device()``
        and it is the user's responsibility to ensure that this is set so that each
        rank has an individual GPU, via ``torch.cuda.set_device()``.
    """

    no_dist = no_dist or (not dist.is_available()) or (not dist.is_initialized())
    if no_dist:
        warnings.warn(
            "torch.distributed is disabled, unavailable or uninitialized, assuming the intent is to load in a single process.",
            stacklevel=2,
        )

    with _profile():
        storage_reader = cast(
            StorageReader, _storage_setup(storage_reader, checkpoint_id, reader=True)
        )

        # All ranks must have the same keys in their `state_dict` provided to
        # this API.  See documentation for more details.
        # Here we simply sort the keys to ensure that all ranks load values in
        # the same order.
        keys = sorted(state_dict.keys())

        stateful_sd = {}
        for key in keys:
            if key not in state_dict:
                continue
            elem = state_dict[key]
            stateful_sd[key] = elem.state_dict() if isinstance(elem, Stateful) else elem

        _load_state_dict(
            state_dict=stateful_sd,
            storage_reader=storage_reader,
            process_group=process_group,
            no_dist=no_dist,
            planner=planner,
        )
        for key in keys:
            if key not in state_dict:
                continue
            elem = state_dict[key]
            if isinstance(elem, Stateful):
                # If the state_dict is a Stateful object,
                # DCP does an in-place load in the original state dict.
                elem.load_state_dict(stateful_sd[key])
            else:
                # Otherwise, replace the state_dict with the loaded state_dict.
                state_dict[key] = stateful_sd[key]