def _init_core_state(
    state: _FSDPState,
    sharding_strategy: ShardingStrategy | None,
    mixed_precision: MixedPrecision | None,
    cpu_offload: CPUOffload | None,
    limit_all_gathers: bool,
    use_orig_params: bool,
    backward_prefetch_limit: int,
    forward_prefetch_limit: int,
) -> _FSDPState:
    # We clamp the strategy to `NO_SHARD` for world size of 1 since they are
    # currently functionally equivalent. This may change if/when we integrate
    # FSDP with MoE.
    if state.world_size == 1:
        if sharding_strategy != ShardingStrategy.NO_SHARD:
            warnings.warn(
                "FSDP is switching to use `NO_SHARD` instead of "
                f"{sharding_strategy or ShardingStrategy.FULL_SHARD} since "
                "the world size is 1.",
                stacklevel=2,
            )
        sharding_strategy = ShardingStrategy.NO_SHARD
    elif sharding_strategy == ShardingStrategy.NO_SHARD:
        warnings.warn(
            "The `NO_SHARD` sharding strategy is deprecated. If having issues, "
            "please use `DistributedDataParallel` instead.",
            FutureWarning,
            # Level 1 is here, level 2 is from `FullyShardedDataParallel`, and
            # level 3 is from the true caller
            stacklevel=3,
        )
    state.sharding_strategy = sharding_strategy or ShardingStrategy.FULL_SHARD
    state.mixed_precision = mixed_precision or MixedPrecision()
    if mixed_precision is not None:
        torch._C._log_api_usage_once(
            f"torch.distributed.fsdp.mixed_precision.{str(state.mixed_precision)}"
        )
    state._use_full_prec_in_eval = (
        os.environ.get(_FSDP_USE_FULL_PREC_IN_EVAL, "") == "1"
    )
    state.cpu_offload = cpu_offload or CPUOffload()
    state.limit_all_gathers = limit_all_gathers
    state._use_orig_params = use_orig_params
    state.training_state = TrainingState.IDLE
    state._is_root = None
    state._free_event_queue = _FreeEventQueue()
    state._debug_level = dist.get_debug_level()
    state._exec_order_data = exec_order_utils._ExecOrderData(
        state._debug_level,
        backward_prefetch_limit,
        forward_prefetch_limit,
    )
    state._unshard_event = None
    # Mapping from fully sharded module to the handles it is responsible to
    # unshard and reshard (see [Note: Fully Sharded Module])
    _fully_sharded_module_to_handle: dict[nn.Module, FlatParamHandle] = {}
    state._fully_sharded_module_to_handle = _fully_sharded_module_to_handle
    # Invariant: `state.params` contains exactly the `FlatParameter`s of the
    # handles in `state._handle`
    _handle: FlatParamHandle | None = None
    state._handle = _handle
    params: list[FlatParameter] = []
    state.params = params
    return state