def _convert_all_state_info(
    fsdp_param_info: FSDPParamInfo,
    gathered_state_info: list[dict[str, StateInfo]],
    input_states: dict[str, Any],
    output_states: dict[str, dict[str, Any]],
) -> tuple[torch.dtype | None, dict[str, list[torch.Tensor | None]]]:
    """
    Given the ``gathered_state_info`` and ``input_states``, the API converted
    the StateInfo into the original state if the state is not a non-scalar
    tensor. For a multi-dimensional tensor, the local state will be stored in
    ``state_buffer`` in a correct order for later allgather purpose.
    """

    state_buffers: dict[str, list[torch.Tensor | None]] = {}

    for fqn, gathered_state in output_states.items():
        state_info = [s[fqn] for s in gathered_state_info]
        all_tensor_states = sorted({n for state in state_info for n in state.tensors})
        empty_ranks: set[int] = set()
        dtype: torch.dtype | None = None
        # First check all the non-scalar states and get the information of
        # states on each rank.
        for state_name in all_tensor_states:
            numels = []
            _empty_ranks: set[int] = set()
            for rank, object_state in enumerate(state_info):
                numels.append(0)
                info = object_state.tensors.get(state_name, None)
                if info is not None:
                    numels[-1] = info.shape.numel()
                    if not dtype:
                        dtype = info.dtype
                    else:
                        if dtype != info.dtype:
                            raise AssertionError(
                                f"Expected dtype == info.dtype, got {dtype} != {info.dtype}"
                            )
                if numels[-1] == 0:
                    _empty_ranks.add(rank)

            if not (not empty_ranks or empty_ranks == _empty_ranks):
                raise AssertionError(
                    f"Expected empty_ranks to be empty or equal to _empty_ranks, got {empty_ranks} vs {_empty_ranks}"
                )
            empty_ranks = _empty_ranks
            if state_name not in state_buffers:
                state_buffers[state_name] = [
                    None for _ in fsdp_param_info.param_indices
                ]
            local_state = input_states[fqn].get(state_name, None)
            # N.B. We need to move the state to compute_device. The reason is
            # not yet clear and we need to figure out why the state may be on a
            # different device.
            if local_state is not None:
                local_state = local_state.to(fsdp_param_info.state.compute_device)
            state_buffers[state_name][fsdp_param_info.param_indices[fqn]] = local_state

        # Restoring the scalar and non-tensor states. If the corresponding
        # non-scalar states do not exist on the rank, we also skip the scalar
        # non-tensor states on that rank.
        for rank, object_state in enumerate(state_info):
            if rank in empty_ranks:
                continue
            for name, non_tensor_value in object_state.non_tensors.items():
                curr_non_tensor_value = gathered_state.get(name, None)
                if not (
                    curr_non_tensor_value is None
                    or curr_non_tensor_value == non_tensor_value
                ):
                    raise AssertionError(
                        f"Rank {rank} has different values for {name}: {non_tensor_value}."
                        + f" Other ranks: {curr_non_tensor_value}"
                    )
                gathered_state[name] = non_tensor_value

            for name, scalar_tensor_value in object_state.scalar_tensors.items():
                curr_scalar_tensor_value = gathered_state.get(name, None)
                if not (
                    curr_scalar_tensor_value is None
                    or torch.equal(scalar_tensor_value, curr_scalar_tensor_value)
                ):
                    raise AssertionError(
                        f"Rank {rank} has different values for {name}: {scalar_tensor_value}."
                        + f" Other ranks: {curr_scalar_tensor_value}"
                    )
                gathered_state[name] = scalar_tensor_value

    return dtype, state_buffers