def _load_optim_state_dict(
    model: nn.Module,
    optimizers: tuple[torch.optim.Optimizer, ...],
    state_dict: OptimizerStateType,
    info: _StateDictInfo,
) -> None:
    if not info.handle_optim:
        return

    for optim in optimizers:
        _init_optim_state(optim)
        if state_dict:
            if _STATE in state_dict:
                optim_state_dict = _split_optim_state_dict(
                    model, optim, state_dict, info
                )
            else:
                optim_state_dict = _unflatten_optim_state_dict(
                    optim, cast(dict[str, ValueType], state_dict), info
                )
        else:
            optim_state_dict = {}
        if info.fsdp_modules:
            # We need to specially handle FlatParameter FSDP as
            # FlatParameter FSDP converts the FQNs.
            for original_fqn, _ in model.named_parameters():
                fqns = _get_fqns(model, original_fqn)
                fqns_with_compiler = _get_fqns(
                    model, original_fqn, skip_compiler_prefix=False
                )
                if fqns == fqns_with_compiler:
                    continue

                if len(fqns) != 1:
                    raise AssertionError(
                        f"Expected 1 FQN for '{original_fqn}', got {len(fqns)}"
                    )
                fqn = fqns.pop()
                fqn_with_compiler = fqns_with_compiler.pop()
                for g in optim_state_dict[_PG]:
                    val = cast(dict[str, Any], g)
                    params = [
                        key.replace(fqn, fqn_with_compiler) for key in val[_PARAMS]
                    ]
                    val[_PARAMS] = params
                osd_state = cast(DictValueType, optim_state_dict[_STATE])
                for k in list(osd_state.keys()):
                    if fqn in k:
                        osd_state[k.replace(fqn, fqn_with_compiler)] = osd_state.pop(k)

            with info.fsdp_context():
                optim_state_dict = FSDP.optim_state_dict_to_load(
                    model, optim, optim_state_dict
                )
        elif info.full_state_dict:
            info.full_state_dict = False
            local_state_dict = _get_optim_state_dict(model, (optim,), info)
            info.full_state_dict = True
            device = None

            def _device(t):
                if t.dim() > 0:
                    nonlocal device
                    if device is None:
                        device = t.device
                    elif device != t.device:
                        raise ValueError("Device mismatch")
                return t

            _ = tree_map_only(torch.Tensor, _device, local_state_dict)
            if device is None:
                raise AssertionError("Expected device to be set")
            flatten_osd, osd_mapping = _flatten_state_dict(optim_state_dict)
            flatten_local_osd, local_osd_mapping = _flatten_state_dict(local_state_dict)
            if info.broadcast_from_rank0:
                _broadcast_state_dict(flatten_osd, flatten_local_osd, device=device)
            else:
                _distribute_state_dict(flatten_osd, flatten_local_osd, device=device)
            # The modifications listed seek to address the problem where optim might possess
            # dissimilar parameters in comparison to optim_state_dict. This is achieved by
            # incorporating differential parameters within local, which may result in optim
            # having additional parameters ultimately.
            for optim_key in flatten_osd:
                if optim_key not in flatten_local_osd:
                    if optim_key not in osd_mapping:
                        raise AssertionError(
                            f"Expected key '{optim_key}' in osd_mapping"
                        )
                    flatten_local_osd[optim_key] = flatten_osd[optim_key]
                    local_osd_mapping[optim_key] = osd_mapping[optim_key]
            optim_state_dict = _unflatten_state_dict(
                flatten_local_osd, local_osd_mapping
            )
            for pg in optim_state_dict[_PG]:
                if _PARAMS not in pg:
                    cast(dict[str, ValueType], pg)[_PARAMS] = []

        # Note that we do not have to convert the FQN back to param id here if
        # order in optim.param_groups[idx][_PARAMS] is the same as the one in
        # optim_state_dict[_PG][idx][_PARAMS].
        _state_dict_fn(optim, "load_state_dict")(state_dict=optim_state_dict)