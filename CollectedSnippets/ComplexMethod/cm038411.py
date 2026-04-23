def init_distributed_environment(
    world_size: int = -1,
    rank: int = -1,
    distributed_init_method: str = "env://",
    local_rank: int = -1,
    backend: str = "nccl",
    timeout: timedelta | None = None,
):
    logger.debug(
        "world_size=%d rank=%d local_rank=%d distributed_init_method=%s backend=%s",
        world_size,
        rank,
        local_rank,
        distributed_init_method,
        backend,
    )
    from vllm.config import get_current_vllm_config_or_none

    config = get_current_vllm_config_or_none()
    enable_elastic_ep = config is not None and config.parallel_config.enable_elastic_ep
    if (
        config is not None
        and config.parallel_config.distributed_executor_backend != "external_launcher"
        and (
            config.parallel_config.nnodes > 1
            or config.parallel_config.data_parallel_size > 1
        )
        and not enable_elastic_ep
    ):
        parallel_config = config.parallel_config
        # adjust to take into account data parallelism
        # offset the rank by the data parallel rank
        rank = parallel_config.data_parallel_rank * world_size + rank
        # adjust the world size to take into account data parallelism
        world_size = parallel_config.world_size_across_dp

        # Use appropriate IP and port based on configuration
        if parallel_config.nnodes > 1:
            ip = parallel_config.master_addr
            port = parallel_config.master_port
            distributed_init_method = get_distributed_init_method(ip, port)
        else:
            ip = parallel_config.data_parallel_master_ip
            port = parallel_config.get_next_dp_init_port()
            distributed_init_method = get_distributed_init_method(ip, port)
            logger.debug(
                "Adjusting world_size=%d rank=%d distributed_init_method=%s for DP",
                world_size,
                rank,
                distributed_init_method,
            )
    if not torch.distributed.is_initialized():
        logger.info(
            "world_size=%d rank=%d local_rank=%d distributed_init_method=%s backend=%s",
            world_size,
            rank,
            local_rank,
            distributed_init_method,
            backend,
        )
        assert distributed_init_method is not None, (
            "distributed_init_method must be provided when initializing "
            "distributed environment"
        )
        if not torch.distributed.is_backend_available(backend):
            logger.warning(
                "Distributed backend %s is not available; falling back to gloo.",
                backend,
            )
            assert torch.distributed.is_gloo_available(), (
                "Fallback Gloo backend is not available."
            )
            backend = "gloo"
        # this backend is used for WORLD
        torch.distributed.init_process_group(
            backend=backend,
            init_method=distributed_init_method,
            world_size=world_size,
            rank=rank,
            timeout=timeout,
        )
        if enable_elastic_ep:
            tp_pp_cpu_group = torch.distributed.new_group(
                backend="gloo", timeout=timeout
            )
            if _node_count(tp_pp_cpu_group) > 1:
                # NOTE(yongji): StatelessGroupCoordinator uses data_parallel_master_ip
                # to initialize all DP/EP groups, hence all ranks within TP/PP group
                # must reside on the same node
                raise RuntimeError(
                    "Elastic EP is not yet supported with multi-node TP/PP"
                )

    # set the local rank
    # local_rank is not available in torch ProcessGroup,
    # see https://github.com/pytorch/pytorch/issues/122816
    if local_rank == -1:
        # local rank not set, this usually happens in single-node
        # setting, where we can use rank as local rank
        local_rank = envs.LOCAL_RANK if distributed_init_method == "env://" else rank

    global _WORLD, _NODE_COUNT, _INNER_DP_WORLD
    if enable_elastic_ep:
        _init_elastic_ep_world(config, local_rank, backend, rank, world_size)
        return
    if _WORLD is None:
        ranks = list(range(torch.distributed.get_world_size()))
        _WORLD = init_world_group(ranks, local_rank, backend)
        if config is not None and config.parallel_config.nnodes > 1:
            _NODE_COUNT = config.parallel_config.nnodes
        else:
            _NODE_COUNT = _node_count(_WORLD.cpu_group)
        logger.debug("Detected %d nodes in the distributed environment", _NODE_COUNT)
    else:
        assert _WORLD.world_size == torch.distributed.get_world_size(), (
            "world group already initialized with a different world size"
        )
    if config is not None and config.parallel_config.nnodes_within_dp > 1:
        if parallel_config.data_parallel_size > 1:
            world_size_inner_dp = parallel_config.world_size
            group_ranks = [
                [dp_rank * world_size_inner_dp + i for i in range(world_size_inner_dp)]
                for dp_rank in range(parallel_config.data_parallel_size)
            ]
            _INNER_DP_WORLD = init_model_parallel_group(
                group_ranks,
                get_world_group().local_rank,
                backend,
                use_message_queue_broadcaster=True,
                group_name="inner_dp_world",
                use_device_communicator=False,
            )
        else:
            _INNER_DP_WORLD = _WORLD