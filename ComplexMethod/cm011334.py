def _checkpointing_subprocess(
        pg_init_info: _ProcessGroupInitInfo,
        parent_conn,
    ) -> None:
        # Phase 1: Process Group Initialization
        # Only needs to execute once during the lifetime of the checkpoint background process.
        try:
            _init_logger(pg_init_info.global_rank)

            # Setup environment variables for process group initialization.
            os.environ["TORCHELASTIC_USE_AGENT_STORE"] = "False"
            os.environ["MASTER_ADDR"] = pg_init_info.tcp_store_master_addr
            os.environ["MASTER_PORT"] = str(pg_init_info.tcp_store_master_port)
            os.environ["LOCAL_RANK"] = str(pg_init_info.local_rank)
            os.environ["RANK"] = str(pg_init_info.global_rank)
            os.environ["WORLD_SIZE"] = str(pg_init_info.world_size)

            logger.info(
                "Initializing dist.ProcessGroup in checkpoint background process on port %s",
                pg_init_info.tcp_store_master_port,
            )
            # NOTE: GLOO backend is enforced here.
            if pg_init_info.use_prefix_store:
                logger.info(
                    "Initializing dist.ProcessGroup in checkpoint background process with prefix store"
                )
                store = PrefixStore(
                    "AsyncCheckpointProcess/",
                    TCPStore(
                        pg_init_info.tcp_store_master_addr,
                        pg_init_info.tcp_store_master_port,
                    ),
                )
                dist.init_process_group(
                    backend=dist.Backend.GLOO,
                    store=store,
                    world_size=pg_init_info.world_size,
                    rank=pg_init_info.global_rank,
                )
            else:
                dist.init_process_group(backend=dist.Backend.GLOO)
            dist.barrier()

            logger.info("Checkpoint background process is running...")
            parent_conn.send(_CheckpointSaveProcessControlOpts.INIT_COMPLETE)

            if pg_init_info.disable_automatic_gc:
                # Disable automatic garbage collection
                # GC can optionally be called manually after each checkpoint
                gc.disable()
                logger.info("Disabled automatic garbage collection")
        except BaseException as e:
            logger.error(
                f"Checkpoint background process failed during initialization: {e}"  # noqa: G004
            )
            parent_conn.send(e)
            return

        # Phase 2: Serving Loop
        try:
            first_request = True
            while True:
                logger.info("Waiting for checkpoint save request...")
                obj = parent_conn.recv()
                if (
                    isinstance(obj, _CheckpointSaveProcessControlOpts)
                    and obj == _CheckpointSaveProcessControlOpts.TERMINATE
                ):
                    logger.info("Terminating the checkpoint background process.")
                    return
                if not isinstance(obj, _AsyncCheckpointRequest):
                    raise AssertionError(
                        f"Expected _AsyncCheckpointRequest, got {type(obj)}"
                    )
                logger.info(
                    f"Received async checkpoint request with id={obj.checkpoint_request_id.checkpoint_id}"  # noqa: G004
                )

                try:
                    response = _AsyncCheckpointProcess._execute_save(
                        obj.staged_state_dict,
                        checkpoint_request_id=obj.checkpoint_request_id,
                        storage_writer=obj.storage_writer,
                        planner=obj.planner,
                        no_dist=obj.no_dist,
                        use_collectives=obj.use_collectives,
                    )
                    parent_conn.send(response)
                    logger.info(
                        f"Completed checkpoint save request for checkpoint_id={obj.checkpoint_request_id}"  # noqa: G004
                    )

                    # in theory this manual gc should not be needed as we shouldn't be leaking anything from checkpointing process
                    if (
                        pg_init_info.disable_automatic_gc
                        and not pg_init_info.disable_manual_gc
                    ):
                        del obj

                        collected_objects = gc.collect()

                        logger.info(
                            f"Manual garbage collection completed - collected {collected_objects} objects."  # noqa: G004
                        )
                        if first_request:
                            # Freeze GC to not check GC for large checkpoint save plans
                            # After freezing, subsequent gc.collect() calls will only scan
                            # NEW objects created after this point, not the frozen save plan
                            logger.info(
                                "First checkpoint request completed - freezing gc"
                            )
                            gc.freeze()
                    first_request = False
                except BaseException as e:
                    logger.error(
                        f"Checkpoint save failed for checkpoint_id={obj.checkpoint_request_id.checkpoint_id}: {e}"  # noqa: G004
                    )
                    parent_conn.send(e)
                    # Continue serving loop - don't exit process
        finally:
            logger.info("Checkpoint background process is shutting down...")
            dist.destroy_process_group()
            parent_conn.close()