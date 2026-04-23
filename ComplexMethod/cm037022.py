def set_forward_context(
    attn_metadata: Any,
    vllm_config: VllmConfig,
    num_tokens: int | None = None,
    num_tokens_across_dp: torch.Tensor | None = None,
    cudagraph_runtime_mode: CUDAGraphMode = CUDAGraphMode.NONE,
    batch_descriptor: BatchDescriptor | None = None,
    ubatch_slices: UBatchSlices | None = None,
    slot_mapping: dict[str, torch.Tensor] | list[dict[str, torch.Tensor]] | None = None,
    skip_compiled: bool = False,
):
    """A context manager that stores the current forward context,
    can be attention metadata, etc.
    Here we can inject common logic for every model forward pass.
    """
    global forward_start_time
    need_to_track_batchsize = track_batchsize and attn_metadata is not None
    if need_to_track_batchsize:
        forward_start_time = time.perf_counter()

    dp_metadata: DPMetadata | None = None
    if (
        vllm_config.parallel_config.data_parallel_size > 1
        and vllm_config.parallel_config.is_moe_model is not False
        and (attn_metadata is not None or num_tokens is not None)
    ):
        # If num_tokens_across_dp hasn't already been initialized, then
        # initialize it here. Both DP padding and Microbatching will be
        # disabled.
        if num_tokens_across_dp is None:
            assert ubatch_slices is None
            assert num_tokens is not None
            _, num_tokens_across_dp, _ = coordinate_batch_across_dp(
                num_tokens_unpadded=num_tokens,
                parallel_config=vllm_config.parallel_config,
                allow_microbatching=False,
            )
            assert num_tokens_across_dp is not None
        dp_metadata = DPMetadata.make(
            vllm_config.parallel_config, num_tokens or 0, num_tokens_across_dp
        )

    # Convenience: if cudagraph is used and num_tokens is given, we can just
    # create a batch descriptor here if not given (there's no harm since if it
    # doesn't match in the wrapper it'll fall through).
    if cudagraph_runtime_mode != CUDAGraphMode.NONE and num_tokens is not None:
        batch_descriptor = batch_descriptor or BatchDescriptor(num_tokens=num_tokens)

    additional_kwargs = current_platform.set_additional_forward_context(
        attn_metadata=attn_metadata,
        vllm_config=vllm_config,
        dp_metadata=dp_metadata,
        num_tokens=num_tokens,
        num_tokens_across_dp=num_tokens_across_dp,
        cudagraph_runtime_mode=cudagraph_runtime_mode,
        batch_descriptor=batch_descriptor,
        ubatch_slices=ubatch_slices,
    )

    forward_context = create_forward_context(
        attn_metadata,
        vllm_config,
        dp_metadata,
        cudagraph_runtime_mode,
        batch_descriptor,
        ubatch_slices,
        slot_mapping,
        additional_kwargs,
        skip_compiled,
    )

    try:
        with (
            override_forward_context(forward_context),
            vllm_config.kernel_config.ir_op_priority.set_priority(),
            vllm.ir.enable_torch_wrap(
                vllm_config.compilation_config.ir_enable_torch_wrap
            ),
        ):
            yield
    finally:
        global last_logging_time, batchsize_logging_interval
        if need_to_track_batchsize:
            batchsize = num_tokens
            # we use synchronous scheduling right now,
            # adding a sync point here should not affect
            # scheduling of the next batch
            synchronize = current_platform.synchronize
            if synchronize is not None:
                synchronize()
            now = time.perf_counter()
            # time measurement is in milliseconds
            batchsize_forward_time[batchsize].append((now - forward_start_time) * 1000)
            if now - last_logging_time > batchsize_logging_interval:
                last_logging_time = now
                forward_stats = []
                for bs, times in batchsize_forward_time.items():
                    if len(times) <= 1:
                        # can be cudagraph / profiling run
                        continue
                    medium = torch.quantile(torch.tensor(times), q=0.5).item()
                    medium = round(medium, 2)
                    forward_stats.append((bs, len(times), medium))
                forward_stats.sort(key=lambda x: x[1], reverse=True)
                if forward_stats:
                    logger.info(
                        (
                            "Batchsize forward time stats "
                            "(batchsize, count, median_time(ms)): %s"
                        ),
                        forward_stats,
                    )