def _unflatten_orig_param_states(
    fsdp_param_info: FSDPParamInfo,
    output_states: dict[str, dict[str, Any]],
    state_name: str,
    shard_state: bool,
    to_save: bool,
    cpu_offload: bool,
) -> None:
    """
    Given a output state dict, ``output_states``, which the keys are FQNs to the
    original parameters (not FlatParameters nor parameter ID), and the values
    are gathered states, unflatten the states to the original dimensions.

    This function performs the unflattening process in-place.
    """
    if not to_save:
        return
    flat_param = fsdp_param_info.handle.flat_param
    fsdp_state = fsdp_param_info.state
    for fqn, gathered_state in output_states.items():
        value = gathered_state[state_name]
        param_idx = fsdp_param_info.param_indices[fqn]

        # TODO: This solution is not general and only apply to PTD TP solution.
        if isinstance(value, DTensor):
            placement = value.placements[0]
            # If gathered state is a DTensor and its TP placement is not Replicate(), we need to
            # gather the tensor on its TP dimension before chunking them into DTensor again.
            if placement != Replicate():
                placement_dim = placement.dim  # type: ignore[attr-defined]
                value.redistribute(placements=(Replicate(),))
                reshape_size = list(flat_param._shapes[param_idx])
                reshape_size[placement_dim] *= value.device_mesh.size(0)
                reshape_size = torch.Size(reshape_size)
                value = value.reshape(reshape_size)
            # If gathered state is a replicate DTensor, we directly reshape it.
            else:
                value = value.reshape(flat_param._shapes[param_idx])
        else:
            # If gathered state is a tensor, we directly reshape it into unflatten state.
            value = value.reshape(flat_param._shapes[param_idx])

        if shard_state:
            osd_config = fsdp_state._optim_state_dict_config
            if getattr(osd_config, "_use_dtensor", False):
                if fsdp_state._device_mesh is None:
                    raise AssertionError(
                        f"Expected _device_mesh to be not None, got {fsdp_state._device_mesh}"
                    )
                value = _ext_chunk_dtensor(
                    value,
                    fsdp_state.rank,
                    fsdp_state._device_mesh,
                    fsdp_state._fsdp_extension,
                )
            else:
                if fsdp_state.process_group is None:
                    raise AssertionError(
                        f"Expected process_group to be not None, got {fsdp_state.process_group}"
                    )
                value = _ext_chunk_tensor(
                    value,
                    fsdp_state.rank,
                    fsdp_state.world_size,
                    fsdp_state._device_handle.device_count(),
                    fsdp_state.process_group,
                    fsdp_state._fsdp_extension,
                )
        elif not cpu_offload:
            with SimpleProfiler.profile("clone"):
                value = value.detach().clone()

        if cpu_offload:
            with SimpleProfiler.profile(SimpleProfiler.Type.D2H):
                value = value.cpu()
        gathered_state[state_name] = value