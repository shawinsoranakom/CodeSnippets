def _local_pre_load_state_dict_hook(
    module: nn.Module,
    fsdp_state: _FSDPState,
    state_dict: dict[str, Any],
    prefix: str,
) -> None:
    """
    This hook finds the local flat_param for this FSDP module from the
    state_dict. The flat_param should be a ShardedTensor. This hook converts
    the ShardedTensor to a tensor. No copy happen unless padding is required.
    """
    _lazy_init(fsdp_state, module)
    _replace_by_prefix(state_dict, prefix, f"{prefix}{FSDP_PREFIX}")
    fqn = f"{prefix}{FSDP_PREFIX}{FLAT_PARAM}"
    if fqn not in state_dict:
        if _has_fsdp_params(fsdp_state, module):
            raise AssertionError(
                "No `FlatParameter` in `state_dict` for this FSDP instance "
                "but it has parameters"
            )
        return
    load_tensor = state_dict[fqn]
    if not isinstance(load_tensor, ShardedTensor):
        raise AssertionError("Tensors in local_state_dict should be ShardedTensor.")

    # Convert the ShardedTensor to a Tensor.
    flat_param = _module_handle(fsdp_state, module).flat_param
    if flat_param is None:
        raise AssertionError("Expected flat_param to be set")
    valid_data_size = flat_param.numel() - flat_param._shard_numel_padded
    shards = load_tensor.local_shards()
    if valid_data_size > 0:
        if not len(shards):
            raise AssertionError(
                "load_local_state_dict assume one shard per ShardedTensor."
            )
        load_tensor = shards[0].tensor

        # Get the metadata of the flat_param to decide whether to pad the loaded
        # tensor.
        if flat_param._shard_numel_padded > 0:
            if load_tensor.numel() >= flat_param.numel():
                raise AssertionError(
                    f"Local shard size = {flat_param.numel()} and the tensor in "
                    f"the state_dict is {load_tensor.numel()}."
                )
            load_tensor = F.pad(load_tensor, [0, flat_param._shard_numel_padded])
    else:
        load_tensor = flat_param
    # TODO: Add DTensor state_dict support for LOCAL_STATE_DICT.
    state_dict[fqn] = load_tensor