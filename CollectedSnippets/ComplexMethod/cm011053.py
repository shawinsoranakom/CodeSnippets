def _communicate_optim_state(
    fsdp_param_info: FSDPParamInfo,
    flat_param_state: dict[str, Any],
) -> _ConsolidatedOptimState:
    """
    Communicates the optimizer state for a flat parameter across ranks. All
    ranks will hold the entire non-sharded optimizer state on GPU.

    If ``N`` is the number of tensor optimizer states in the optimizer state
    dict, then the communication complexity is 0 if ``N = 0`` and ``N + 1``
    otherwise (where the plus 1 comes from all-gathering the padding per rank).

    Args:
        fsdp_param_info (FSDPParamInfo): The FSDP state, the handle, and a
            mapping from FQN to original parameter index.
        flat_param_state (Dict[str, Any]): The entry in the "state" part of the
            optimizer state dict corresponding to the flat parameter.

    Returns:
        ConsolidatedOptimState: Consolidated optimizer state for the target
        flat parameter.
    """
    fsdp_state = fsdp_param_info.state
    flat_param = fsdp_param_info.handle.flat_param
    state = _ConsolidatedOptimState()
    tensor_state, zero_dim_tensor_state, non_tensor_state = (
        state.tensor_state,
        state.zero_dim_tensor_state,
        state.non_tensor_state,
    )

    for state_name, value in sorted_items(flat_param_state):
        # Positive-dimension tensor state: communicate across ranks
        if torch.is_tensor(value) and value.dim() > 0:
            # If the parameter is not sharded, then neither is the
            # positive-dimension tensor state, so no need to communicate it --
            # we take the target rank's value
            if (
                fsdp_state.world_size == 1
                or fsdp_state.sharding_strategy == ShardingStrategy.NO_SHARD
            ):
                tensor_state[state_name] = value
                continue
            if fsdp_state.compute_device is None:
                raise AssertionError("compute_device has not been initialized")
            if value.device.type != fsdp_state.compute_device.type:
                value = value.to(fsdp_state.compute_device)
            # Assume that positive-dimension tensor optimizer state
            # has the same shape as the sharded flat parameter
            buffer_size = flat_param._full_param_padded.size()  # type: ignore[attr-defined]
            tensor_buffer = value.new_zeros(*buffer_size)
            dist.all_gather_into_tensor(
                tensor_buffer, value, group=fsdp_state.process_group
            )
            fsdp_state._device_handle.synchronize()
            unpadded_numel = cast(
                nn.Parameter, flat_param._unpadded_unsharded_size
            ).numel()
            tensor_state[state_name] = tensor_buffer[:unpadded_numel]
        # Zero-dimension tensor state and non-tensor state: take this rank's
        # value directly
        else:
            if _is_zero_dim_tensor(value):
                zero_dim_tensor_state[state_name] = value.detach().clone()
            else:
                non_tensor_state[state_name] = value
    return state