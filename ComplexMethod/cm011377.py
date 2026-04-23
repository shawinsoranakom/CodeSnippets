def _subprocess(
        sub_rank: int,
        rank_info: RankInfo,
        parent_pipe: Connection,
        subprocess_init_fn: Callable[[Any], None],
        subprocess_init_args: tuple[Any, ...],
        checkpoint_writer_init_fn: Callable[..., CheckpointWriter],
        checkpoint_writer_init_args: dict[str, Any],
    ) -> None:
        logger.debug(
            "Checkpoint subprocess started for rank %d/%d (PID: %d)",
            rank_info.global_rank,
            rank_info.global_world_size,
            os.getpid(),
        )

        if sub_rank != 0:
            raise AssertionError("We need only one checkpointer per parent training")
        request = WorkerRequest(request_type=RequestType.PING, payload={})

        try:
            # Calling initialize callback, so we can perform app-specific initialization of the subprocess.
            subprocess_init_fn(*subprocess_init_args)

            # Initialize checkpoint writer - automatically include rank_info in init_args
            writer_init_args = dict(checkpoint_writer_init_args)
            if "rank_info" not in writer_init_args:
                writer_init_args["rank_info"] = rank_info
            checkpoint_writer = checkpoint_writer_init_fn(**writer_init_args)

            while True:
                request = parent_pipe.recv()

                if request.request_type == RequestType.PING:
                    parent_pipe.send(
                        WorkerResponse(request_type=RequestType.PING, success=True)
                    )
                elif request.request_type == RequestType.WRITE_CHECKPOINT:
                    path = request.payload["path"]
                    logger.info("Writing checkpoint to %s", path)

                    checkpoint_writer.write(
                        path=path,
                        state_dict=request.payload["state_dict"],
                        **request.payload["kwargs"],
                    )

                    logger.info("Checkpoint written successfully to %s", path)
                    parent_pipe.send(
                        WorkerResponse(RequestType.WRITE_CHECKPOINT, success=True)
                    )
                elif request.request_type == RequestType.TERMINATE_PROCESS:
                    logger.debug("Received termination request.")
                    parent_pipe.send(
                        WorkerResponse(RequestType.TERMINATE_PROCESS, success=True)
                    )
                    logger.info("Subprocess terminated gracefully")
                    break
                else:
                    error_msg = f"Unknown request type: {request.request_type}"
                    logger.error(error_msg)
                    raise ValueError(error_msg)

        except Exception as e:
            error_text = traceback.format_exc()
            logger.error(
                "Exception in subprocess  (%s): %s", type(e).__name__, error_text
            )

            # Communicating exception via the queue to the main process
            parent_pipe.send(
                WorkerResponse(
                    request_type=request.request_type,
                    success=False,
                    error_msg=error_text,
                )
            )
            parent_pipe.close()
            logger.exception("Subprocess terminated due to exception")