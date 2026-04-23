def _share_state_and_init_handle_attrs(
    root_state: _FSDPState,
    root_module: nn.Module,
) -> None:
    """
    Shares data structure state from the ``root_state`` to all FSDP states in
    ``root_module`` 's module tree, and initializes handle attributes. These
    are done together to require a single loop over the states.
    """
    handle = root_state._handle
    if handle:
        handle.init_flat_param_attributes()
    attr_name_to_values: dict[str, set[Any]] = {}
    for attr_name in HOMOGENEOUS_ATTR_NAMES:
        attr_name_to_values[attr_name] = set()
    root_state._all_handles = root_state._exec_order_data.all_handles  # share reference
    # Update _has_optim_in_backward for each handle.
    for handle in root_state._all_handles:
        flat_param = handle.flat_param
        if hasattr(flat_param, "_in_backward_optimizers"):
            raise RuntimeError(
                "FSDP optimizer in backward only supported with use_orig_params=True!"
            )
        handle._has_optim_in_backward = flat_param._params is not None and any(
            hasattr(param, "_in_backward_optimizers") for param in flat_param._params
        )
        if handle._has_optim_in_backward:
            torch._C._log_api_usage_once("fsdp.optimizer_in_backward")
    for fsdp_state in root_state._all_fsdp_states:
        for attr_name in HOMOGENEOUS_ATTR_NAMES:
            _p_assert(
                hasattr(fsdp_state, attr_name),
                f"FSDP state missing attribute {attr_name}",
            )
            attr_name_to_values[attr_name].add(getattr(fsdp_state, attr_name))
        if fsdp_state is root_state:
            continue
        # Relax the assert for non-root FSDP instances in case the nested
        # initialized module is wrapped again in FSDP later (e.g. after
        # training to run inference)
        _p_assert(
            fsdp_state._is_root is None or not fsdp_state._is_root,
            "Non-root FSDP instance's `_is_root` should not have been "
            "set yet or should have been set to `False`",
        )
        fsdp_state._is_root = False
        fsdp_state._unshard_stream = root_state._unshard_stream
        fsdp_state._post_backward_stream = root_state._post_backward_stream
        fsdp_state._pre_unshard_stream = root_state._pre_unshard_stream
        fsdp_state._all_reduce_stream = root_state._all_reduce_stream
        fsdp_state._default_stream = root_state._default_stream
        fsdp_state._exec_order_data = root_state._exec_order_data
        fsdp_state._free_event_queue = root_state._free_event_queue
        if fsdp_state._fsdp_extension is not None:
            fsdp_state._fsdp_extension.compute_stream = root_state._default_stream
        handle = fsdp_state._handle
        if handle:
            handle.init_flat_param_attributes()
    for attr_name, attr_values in attr_name_to_values.items():
        if len(attr_values) != 1:
            raise ValueError(
                f"Expects one homogeneous value for {attr_name} but got {attr_values}"
            )