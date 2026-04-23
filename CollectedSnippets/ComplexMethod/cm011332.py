def async_save(
    state_dict: STATE_DICT_TYPE,
    *,
    checkpoint_id: str | os.PathLike | None = None,
    storage_writer: StorageWriter | None = None,
    planner: SavePlanner | None = None,
    process_group: dist.ProcessGroup | None = None,
    async_checkpointer_type: AsyncCheckpointerType = AsyncCheckpointerType.THREAD,
    async_stager: AsyncStager | None = None,
    no_dist: bool = False,
    use_collectives: bool = True,
) -> Future | AsyncSaveResponse:
    """Asynchronous version of ``save``. This code first de-stages the state_dict on to the
    staging storage (defaults to CPU memory), and then calls the `save` in a separate thread.

    .. warning::
        This feature is experimental and subject to change.
        MUST CALL CLOSE AFTER LAST CHECKPOINT IS SAVED

    Args:
        state_dict (Dict[str, Any]): The state_dict to save.
        checkpoint_id (Union[str, os.PathLike, None]):
            The ID of this checkpoint instance. The meaning of the checkpoint_id
            depends on the storage. It can be a path to a folder or to a file.
            It can also be a key if the storage is a key-value store.
            (Default: ``None``)
        storage_writer (Optional[StorageWriter]):
            Instance of StorageWriter used to perform 'stage' and  'save'. If
            this is not specified, DCP will automatically infer the writer based on the
            checkpoint_id. If checkpoint_id is also None, an exception will
            be raised. (Default: ``None``)
        planner (Optional[SavePlanner]):
            Instance of SavePlanner. If this is not specified, the default
            planner will be used. (Default: ``None``)
        process_group (Optional[ProcessGroup]):
            ProcessGroup to be used for cross-rank synchronization.
            (Default: ``None``)
        async_checkpointer_type (AsyncCheckpointerType):
            whether to do checkpoint in separate thread or process
            (Default: ``AsyncCheckpointerType.THREAD``)
        async_stager (AsyncStager):
            provides staging implementation. If storage_writer implements AsyncStager
            and async_stager is provided, async_stager will be used for staging
        no_dist (bool):
            If ``True``, this function will assume the intent is to save
            a checkpoint on a single rank/process.
            (Default: ``False``)
        use_collectives: If False, Save the checkpoint without rank coordination. (Default: ``True``)
            This configuration is experimental and should be used with caution.
            It will change the format of the saved checkpoint and may not be backward compatible.

    Returns:
        Future: A future holding the resultant Metadata object from `save`.

    Example:
        >>> # xdoctest: +SKIP
        >>> my_model = MyModule()

        >>> state_dict = {"model": my_model}

        >>> fs_storage_writer = torch.distributed.checkpoint.FileSystemWriter(
        ...     "/checkpoint/1"
        ... )
        >>> checkpoint_future = torch.distributed.checkpoint.async_save(
        >>>     state_dict=state_dict,
        >>>     storage_writer=fs_storage_writer,
        >>> )
        >>>
        >>> # ... do some work ...
        >>>
        >>> checkpoint_future.result()

    """
    torch._C._log_api_usage_once("torch.distributed.checkpoint.async_save")

    if dist.is_available() and dist.is_initialized():
        pg = process_group or _get_default_group()
        if torch.device("cpu") not in pg._device_types:
            raise AssertionError(
                "A CPU backend must be enabled for async save; try initializing process group with 'cpu:gloo,cuda:nccl'"
            )

    if async_stager is None:
        if storage_writer is not None and isinstance(storage_writer, AsyncStager):
            # bwc with old storage_writers
            async_stager = storage_writer
        else:
            async_stager = DefaultStager(
                StagingOptions(
                    False,
                    False,
                    False,
                    False,
                )
            )

    state_dict = _stateful_to_state_dict(state_dict)

    @_dcp_method_logger(log_exceptions=True)
    def stage_state_dict() -> Future[STATE_DICT_TYPE] | STATE_DICT_TYPE:
        return async_stager.stage(state_dict)

    staging_future_or_state_dict = stage_state_dict()

    upload_executor: _AsyncCheckpointExecutor = (
        _ProcessBasedAsyncCheckpointExecutor()
        if async_checkpointer_type == AsyncCheckpointerType.PROCESS
        else _ThreadBasedAsyncCheckpointExecutor()
    )

    upload_future: Future = upload_executor.execute_save(
        staging_future_or_state_dict,
        checkpoint_id=checkpoint_id,
        storage_writer=storage_writer,
        planner=planner,
        process_group=process_group,
        no_dist=no_dist,
        use_collectives=use_collectives,
    )

    if isinstance(staging_future_or_state_dict, Future):
        staging_future = staging_future_or_state_dict
        return_staging_future: Future[None] = Future()

        def callback(
            original_staging_future: Future[STATE_DICT_TYPE],
            return_staging_future: Future[None] = return_staging_future,
        ):
            try:
                original_staging_future.result()
                return_staging_future.set_result(None)
            except Exception as e:
                return_staging_future.set_exception(e)

        if not staging_future.done():
            staging_future.add_done_callback(callback)
        else:
            return_staging_future.set_result(None)

        # return new AsyncSaveResponse for users using new ZOC implementation
        return AsyncSaveResponse(
            staging_completion=return_staging_future, upload_completion=upload_future
        )
    else:

        @_dcp_method_logger(log_exceptions=True)
        def maybe_synchronize_staging():
            if async_stager.should_synchronize_after_execute:
                async_stager.synchronize_staging()

        maybe_synchronize_staging()
        return upload_future