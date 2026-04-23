def _post_state_dict_hook(
    module: nn.Module,
    state_dict: dict[str, Any],
    prefix: str,
    *args: Any,
) -> dict[str, Any]:
    """
    _post_state_dict_hook() is called after the state_dict() of this
    FSDP module is executed. ``fsdp_state._state_dict_type`` is used to decide
    what postprocessing will be done.
    """
    fsdp_state = _get_module_fsdp_state_if_fully_sharded_module(module)
    if fsdp_state.sharding_strategy == ShardingStrategy.NO_SHARD:
        context = _replace_with_full_state_dict_type(fsdp_state)
        warnings.warn(
            "When using ``NO_SHARD`` for ``ShardingStrategy``, full_state_dict will "
            "be returned.",
            stacklevel=2,
        )
    else:
        context = contextlib.nullcontext()

    with context:
        _post_state_dict_hook_fn = {
            StateDictType.FULL_STATE_DICT: _full_post_state_dict_hook,
            StateDictType.LOCAL_STATE_DICT: _local_post_state_dict_hook,
            StateDictType.SHARDED_STATE_DICT: _sharded_post_state_dict_hook,
        }
        processed_state_dict = _post_state_dict_hook_fn[fsdp_state._state_dict_type](
            module, fsdp_state, state_dict, prefix
        )

    if fsdp_state._is_root:
        logger.info("FSDP finished processing state_dict(), prefix=%s", prefix)
        for key, tensor in sorted(processed_state_dict.items()):
            if key.startswith(prefix) and isinstance(tensor, torch.Tensor):
                local_shape = tensor.shape
                device = None
                if isinstance(tensor, ShardedTensor):
                    local_shape = None
                    shards = tensor.local_shards()
                    if shards:
                        local_shape = shards[0].tensor.shape
                        device = shards[0].tensor.device
                elif isinstance(tensor, DTensor):
                    local_shape = tensor.to_local().shape
                    device = tensor.device
                else:
                    device = tensor.device
                logger.info(
                    "FQN=%s: type=%s, shape=%s, local_shape=%s, dtype=%s, device=%s",
                    key,
                    type(tensor),
                    tensor.shape,
                    local_shape,
                    tensor.dtype,
                    device,
                )

    return processed_state_dict