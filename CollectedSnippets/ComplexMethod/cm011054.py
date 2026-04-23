def _unflatten_communicated_optim_state(
    fsdp_param_info: FSDPParamInfo,
    state: _ConsolidatedOptimState,
    shard_state: bool,
) -> list[dict[str, Any]]:
    """
    Unflattens the communicated optimizer state (given by ``tensor_state``,
    ``non_tensor_state``, and ``zero_dim_tensor_state``) for a single flat
    parameter. This should only be called on the target rank.

    Args:
        fsdp_param_info (FSDPParamInfo): The FSDP state, the handle, and a
            mapping from FQN to original parameter index.
        state (_ConsolidatedOptimState): Consolidated optimizer state.

    Returns:
        List[Dict[str, Any]]: A :class:`list` holding the entries in the
        "state" part of the optimizer state dict corresponding to the
        unflattened parameters comprising the flat parameter. The final
        optimizer state dict will need to map these entries using the proper
        unflattened parameter IDs.
    """
    fsdp_state = fsdp_param_info.state
    handle = fsdp_param_info.handle
    flat_param = handle.flat_param
    unflat_param_state: list[dict[str, Any]] = []
    flat_param_views: dict[str, Iterator] = {}
    num_unflat_params = flat_param._num_params
    tensor_state, zero_dim_tensor_state, non_tensor_state = (
        state.tensor_state,
        state.zero_dim_tensor_state,
        state.non_tensor_state,
    )

    for _ in range(num_unflat_params):
        unflat_state_param = {}
        # Add positive-dimension tensor state: unflatten with views
        for state_name, flat_tensor in sorted_items(tensor_state):
            views_generated = state_name in flat_param_views
            if not views_generated:
                views = handle._get_unflat_views(flat_tensor)
                flat_param_views[state_name] = views
            else:
                views = flat_param_views[state_name]
            optim_state: torch.Tensor | ShardedTensor | DTensor = next(views)
            if shard_state:
                osd_config = fsdp_state._optim_state_dict_config
                if getattr(osd_config, "_use_dtensor", False):
                    if fsdp_state._device_mesh is None:
                        raise AssertionError(
                            f"Expected _device_mesh to be not None, got {fsdp_state._device_mesh}"
                        )
                    optim_state = _ext_chunk_dtensor(
                        optim_state,
                        fsdp_state.rank,
                        fsdp_state._device_mesh,
                        fsdp_state._fsdp_extension,
                    )
                else:
                    if fsdp_state.process_group is None:
                        raise AssertionError(
                            f"Expected process_group to be not None, got {fsdp_state.process_group}"
                        )
                    optim_state = _ext_chunk_tensor(
                        optim_state,
                        fsdp_state.rank,
                        fsdp_state.world_size,
                        fsdp_state._device_handle.device_count(),
                        fsdp_state.process_group,
                        fsdp_state._fsdp_extension,
                    )
            unflat_state_param[state_name] = optim_state

        # Add zero-dimension tensor state: take the target rank's value
        unflat_state_param.update(sorted_items(zero_dim_tensor_state))
        # Add non-tensor state: take the target rank's value
        unflat_state_param.update(sorted_items(non_tensor_state))
        unflat_param_state.append(unflat_state_param)
    return unflat_param_state