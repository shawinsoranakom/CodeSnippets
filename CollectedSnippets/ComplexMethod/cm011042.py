def _common_unshard_post_state_dict_hook(
    module: nn.Module,
    fsdp_state: _FSDPState,
    state_dict: dict[str, Any],
    prefix: str,
    param_hook: Callable,
) -> dict[str, Any]:
    """
    The post-state_dict flow that shared by all state_dict types that require
    ``_unshard_fsdp_state_params()``. FULL_STATE_DICT and SHARDED_STATE_DICT use this
    hook.
    """
    _replace_by_prefix(state_dict, prefix + f"{FSDP_PREFIX}", prefix)
    # Return early for trivial cases
    if not state_dict or not _has_fsdp_params(fsdp_state, module):
        if _should_unshard_params(fsdp_state):
            _exit_unshard_params_ctx(module, fsdp_state)
        return state_dict

    # If a rank does not have unsharded parameters(when `rank0_only=True`
    # and `rank != 0`), then the rank only needed to participate in the
    # all-gather and does not need to save the # state dict. We simply check
    # rank0_only to ensure this issue.
    rank0_only = (
        fsdp_state._state_dict_type == StateDictType.FULL_STATE_DICT
        and cast(FullStateDictConfig, fsdp_state._state_dict_config).rank0_only
    )
    # no_fsdp_return means the state_dict returned by this rank should contain
    # only non-FSDP controlled parameters and buffers.
    no_fsdp_return = rank0_only and fsdp_state.rank != 0
    if no_fsdp_return and not fsdp_state._use_orig_params:
        for clean_key in fsdp_state._buffer_names:
            # This is a hack to support activation checkpoint.
            clean_key = clean_key.replace(
                f"{checkpoint_wrapper._CHECKPOINT_PREFIX}.", ""
            )
            state_dict.pop(f"{prefix}{clean_key}", None)
        # Non-zero ranks have flat_param key when rank0_only=True, because rank0_only=True is
        # passed in to unshard context, but nonzero ranks reshard early, causing this flat_param
        # to appear in state_dict.
        state_dict.pop(f"{prefix}{FLAT_PARAM}")
        _exit_unshard_params_ctx(module, fsdp_state)
        return state_dict

    # Loop only the parameters saved in this instance's wrapped module to
    # avoid processing buffers.
    for fqn, param_name, module_name in _param_name_infos(module, fsdp_state):
        fqn = f"{prefix}{fqn}"
        if no_fsdp_return:
            state_dict.pop(fqn)
            continue
        if fqn not in state_dict:
            raise AssertionError(
                f"FSDP assumes {fqn} is in the state_dict but the state_dict only "
                f"has {state_dict.keys()}. "
                f"prefix={prefix}, module_name={module_name}, "
                f"param_name={param_name} rank={fsdp_state.rank}."
            )

        param_hook(state_dict, prefix, fqn)

    if _should_unshard_params(fsdp_state):
        _exit_unshard_params_ctx(module, fsdp_state)

    cpu_device = torch.device("cpu")
    buffer_clean_fqns = []
    buffers = []
    for clean_key in fsdp_state._buffer_names:
        # This is a hack to support activation checkpoint.
        clean_key = clean_tensor_name(clean_key)
        fqn = f"{prefix}{clean_key}"
        if fqn not in state_dict:
            # A buffer can be registered as non-persistent.
            continue
        if no_fsdp_return:
            state_dict.pop(fqn)
        else:
            buffer = state_dict[fqn]
            if (
                fsdp_state._state_dict_config.offload_to_cpu
                and buffer.device != cpu_device
            ):
                state_dict[fqn] = buffer.to(cpu_device)
            # skip upcasting for ignored buffers
            if clean_key not in fsdp_state._ignored_buffer_names:
                buffer_clean_fqns.append(clean_key)
                buffers.append(state_dict[fqn])

    if buffers:
        mixed_precision_enabled_for_buffers = (
            fsdp_state._mixed_precision_enabled_for_buffers()
            if not _is_composable(fsdp_state)
            else (fsdp_state.mixed_precision.buffer_dtype is not None)
        )
        if mixed_precision_enabled_for_buffers:
            buffer_dtypes = _get_orig_buffer_dtypes(fsdp_state, buffer_clean_fqns)
            _cast_buffers_to_dtype_and_device(
                buffers, buffer_dtypes, fsdp_state.compute_device
            )
            for buffer, clean_fqn in zip(buffers, buffer_clean_fqns):
                fqn = f"{prefix}{clean_fqn}"
                logger.info("FSDP is casting the dtype of %s to %s", fqn, buffer.dtype)
                state_dict[fqn] = buffer.clone()
    return state_dict