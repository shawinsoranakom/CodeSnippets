def initialize_model_parallel(
    tensor_model_parallel_size: int = 1,
    pipeline_model_parallel_size: int = 1,
    prefill_context_model_parallel_size: int = 1,
    decode_context_model_parallel_size: int | None = 1,
    backend: str | None = None,
) -> None:
    """
    Initialize model parallel groups.

    Arguments:
        tensor_model_parallel_size: number of GPUs used for tensor model
            parallelism.
        pipeline_model_parallel_size: number of GPUs used for pipeline model
            parallelism.
        backend: name of torch distributed communication backend.

    Let's say we have a total of 8 GPUs denoted by g0 ... g7 and we
    use 2 GPUs to parallelize the model tensor, and 4 GPUs to parallelize
    the model pipeline. The present function will
    create 4 tensor model-parallel groups and 2 pipeline model-parallel groups:
        4 tensor model-parallel groups:
            [g0, g1], [g2, g3], [g4, g5], [g6, g7]
        2 pipeline model-parallel groups:
            [g0, g2, g4, g6], [g1, g3, g5, g7]
    Note that for efficiency, the caller should make sure adjacent ranks
    are on the same DGX box. For example if we are using 2 DGX-1 boxes
    with a total of 16 GPUs, rank 0 to 7 belong to the first box and
    ranks 8 to 15 belong to the second box.
    """
    # Get world size and rank. Ensure some consistencies.
    assert torch.distributed.is_initialized()

    from vllm.config import get_current_vllm_config

    config = get_current_vllm_config()
    data_parallel_size = config.parallel_config.data_parallel_size
    enable_elastic_ep = config.parallel_config.enable_elastic_ep
    parallel_config = config.parallel_config
    coord_store: Store | None = None
    if enable_elastic_ep:
        coord_store = get_cached_tcp_store_client(
            parallel_config.data_parallel_master_ip,
            parallel_config._coord_store_port,
        )
        # Use stateless world group for global information
        world_size = get_world_group().world_size
        rank = get_world_group().rank
        backend = backend or "nccl"
        tp_pp_pcp_size = (
            tensor_model_parallel_size
            * pipeline_model_parallel_size
            * prefill_context_model_parallel_size
        )
        local_all_ranks = torch.arange(tp_pp_pcp_size).reshape(
            pipeline_model_parallel_size,
            prefill_context_model_parallel_size,
            tensor_model_parallel_size,
        )
    else:
        world_size = torch.distributed.get_world_size()
        rank = torch.distributed.get_rank()
        backend = backend or torch.distributed.get_backend(
            get_world_group().device_group
        )

    # the layout order is: ExternalDP x DP x PP x TP
    # ExternalDP is the data parallel group that is not part of the model,
    # every dp rank can generate independently (in verl integration).
    # DP is the data parallel group that is part of the model,
    # all the ranks in the same DP group should generate simultaneously,
    # i.e. the `generate` call in the same DP group should be called together,
    # otherwise it will cause deadlock.
    # to get group_ranks for each dimension, transpose that dimension to the
    # last dimension, then reshape to 2D, then unbind the last dimension
    all_ranks = torch.arange(world_size).reshape(
        -1,
        data_parallel_size,
        pipeline_model_parallel_size,
        prefill_context_model_parallel_size,
        tensor_model_parallel_size,
    )  # noqa

    # Build the tensor model-parallel groups.
    global _TP
    assert _TP is None, "tensor model parallel group is already initialized"
    group_ranks = all_ranks.view(-1, tensor_model_parallel_size).unbind(0)
    group_ranks = [x.tolist() for x in group_ranks]
    if enable_elastic_ep:
        group_ranks = local_all_ranks.view(-1, tensor_model_parallel_size).unbind(0)
        group_ranks = [x.tolist() for x in group_ranks]
    # message queue broadcaster is only used in tensor model parallel group
    _TP = init_model_parallel_group(
        group_ranks,
        get_world_group().local_rank,
        backend,
        use_message_queue_broadcaster=True,
        group_name="tp",
    )

    # Build the DCP model-parallel groups.
    global _DCP
    assert _DCP is None, "decode context model parallel group is already initialized"
    # Note(hc): In the current implementation of decode context parallel,
    # dcp_size must not exceed tp_size, because the world size does not
    # change by DCP, it simply reuses the GPUs of TP group, and split one
    # TP group into tp_size//dcp_size DCP groups.
    group_ranks = all_ranks.reshape(-1, decode_context_model_parallel_size).unbind(0)
    group_ranks = [x.tolist() for x in group_ranks]
    if enable_elastic_ep:
        group_ranks = local_all_ranks.reshape(
            -1, decode_context_model_parallel_size
        ).unbind(0)
        group_ranks = [x.tolist() for x in group_ranks]
    _DCP = init_model_parallel_group(
        group_ranks,
        get_world_group().local_rank,
        backend,
        use_message_queue_broadcaster=True,
        group_name="dcp",
    )

    global _PCP
    assert _PCP is None, "prefill context parallel group is already initialized"
    group_ranks = (
        all_ranks.transpose(3, 4)
        .reshape(-1, prefill_context_model_parallel_size)
        .unbind(0)
    )
    group_ranks = [x.tolist() for x in group_ranks]
    if enable_elastic_ep:
        group_ranks = (
            local_all_ranks.transpose(1, 2)
            .reshape(-1, prefill_context_model_parallel_size)
            .unbind(0)
        )
        group_ranks = [x.tolist() for x in group_ranks]
    _PCP = init_model_parallel_group(
        group_ranks, get_world_group().local_rank, backend, group_name="pcp"
    )

    # Build the pipeline model-parallel groups.
    global _PP
    assert _PP is None, "pipeline model parallel group is already initialized"
    group_ranks = (
        all_ranks.transpose(2, 4).reshape(-1, pipeline_model_parallel_size).unbind(0)
    )
    group_ranks = [x.tolist() for x in group_ranks]
    if enable_elastic_ep:
        group_ranks = (
            local_all_ranks.transpose(0, 2)
            .reshape(-1, pipeline_model_parallel_size)
            .unbind(0)
        )
        group_ranks = [x.tolist() for x in group_ranks]
    _PP = init_model_parallel_group(
        group_ranks, get_world_group().local_rank, backend, group_name="pp"
    )

    global _DP
    assert _DP is None, "data parallel group is already initialized"
    group_ranks = all_ranks.transpose(1, 4).reshape(-1, data_parallel_size).unbind(0)
    group_ranks = [x.tolist() for x in group_ranks]
    if enable_elastic_ep:
        _DP = _init_stateless_group(
            group_ranks,
            "dp",
            parallel_config.data_parallel_master_ip,
            backend,
            coord_store=coord_store,
        )
    else:
        _DP = init_model_parallel_group(
            group_ranks, get_world_group().local_rank, backend, group_name="dp"
        )

    global _EP
    assert _EP is None, "expert parallel group is already initialized"
    # Don't create EP group for dense models.
    if config.model_config is None or config.model_config.is_moe:
        group_ranks = (
            all_ranks.transpose(1, 2)
            .reshape(
                -1,
                data_parallel_size
                * prefill_context_model_parallel_size
                * tensor_model_parallel_size,
            )
            .unbind(0)
        )
        group_ranks = [x.tolist() for x in group_ranks]
        if enable_elastic_ep:
            _EP = _init_stateless_group(
                group_ranks,
                "ep",
                parallel_config.data_parallel_master_ip,
                backend,
                coord_store=coord_store,
            )
        else:
            _EP = init_model_parallel_group(
                group_ranks, get_world_group().local_rank, backend, group_name="ep"
            )

        # Create EPLB group with the same ranks as EP if EPLB is enabled.
        # This is a separate process group to isolate EPLB communications
        # from MoE forward pass collectives and prevent deadlocks when
        # using torch.distributed in execution with torch.distributed in EPLB.
        global _EPLB
        assert _EPLB is None, "EPLB group is already initialized"
        if config.parallel_config.enable_eplb:
            if enable_elastic_ep:
                _EPLB = _init_stateless_group(
                    group_ranks,
                    "eplb",
                    parallel_config.data_parallel_master_ip,
                    backend,
                    coord_store=coord_store,
                )
            else:
                _EPLB = init_model_parallel_group(
                    group_ranks,
                    get_world_group().local_rank,
                    backend,
                    group_name="eplb",
                )
    # If no EP group needed, _EP remains None
    # If no EPLB group needed, _EPLB remains None

    logger.info_once(
        "rank %s in world size %s is assigned as "
        "DP rank %s, PP rank %s, PCP rank %s, "
        "TP rank %s, EP rank %s, EPLB rank %s",
        rank,
        world_size,
        _DP.rank_in_group,
        _PP.rank_in_group,
        _PCP.rank_in_group,
        _TP.rank_in_group,
        _EP.rank_in_group if _EP is not None else "N/A",
        _EPLB.rank_in_group if _EPLB is not None else "N/A",
    )