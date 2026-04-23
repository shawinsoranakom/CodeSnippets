def determine_expert_placement_strategy(
    expert_placement_strategy: ExpertPlacementStrategy,
    moe_parallel_config: FusedMoEParallelConfig,
    num_expert_group: int | None,
    num_redundant_experts: int,
    enable_eplb: bool,
) -> ExpertPlacementStrategy:
    if expert_placement_strategy == "round_robin":
        round_robin_supported = (
            (num_expert_group is not None and num_expert_group > 1)
            and num_redundant_experts == 0
            and not enable_eplb
        )

        if not round_robin_supported:
            logger.warning(
                "Round-robin expert placement is only supported for "
                "models with multiple expert groups and no redundant "
                "experts. Falling back to linear expert placement."
            )
            return "linear"
        if (
            moe_parallel_config.use_all2all_kernels
            and not moe_parallel_config.use_deepep_ll_kernels
            and not moe_parallel_config.use_nixl_ep_kernels
        ):
            logger.warning(
                "Round-robin expert placement currently only supports "
                "the DeepEP low-latency or NIXL EP backend, but '%s' was configured. "
                "Falling back to linear expert placement.",
                moe_parallel_config.all2all_backend,
            )
            return "linear"

    return expert_placement_strategy