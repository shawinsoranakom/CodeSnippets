def _load_model_state_dict(
    model: nn.Module,
    state_dict: dict[str, ValueType],
    info: _StateDictInfo,
) -> _IncompatibleKeys:
    if not info.handle_model or (not state_dict and not info.broadcast_from_rank0):
        return _IncompatibleKeys({}, {})

    local_state_dict = {}
    for key, value in _iterate_valid_model_state(model, info.dsd_fqn_modifiers):
        fqns = _get_fqns(model, key, info.dsd_fqn_modifiers)
        fqns_with_prefix = _get_fqns(
            model,
            key,
            info.dsd_fqn_modifiers,
            skip_ddp_prefix=False,
            skip_compiler_prefix=False,
        )

        for fqn, fqn_with_prefix in zip(fqns, fqns_with_prefix):
            if (
                not info.broadcast_from_rank0 or dist.get_rank() == 0
            ) and fqn != fqn_with_prefix:
                load_value = state_dict.pop(fqn, None)
                if load_value is None:
                    if info.strict:
                        raise RuntimeError(f"Missing key: {fqn}.")
                else:
                    state_dict[fqn_with_prefix] = load_value
            local_state_dict[fqn_with_prefix] = value

    assign = False
    if info.broadcast_from_rank0 or info.full_state_dict:
        devices = set()
        for value in local_state_dict.values():
            if torch.is_tensor(value) and value.dim() > 0:
                devices.add(value.device)
        # In lora state_dict, there could be multiple devices, with meta device inside.
        # Take the other device in the broadcast/distribtue, and set assign to True
        if torch.device("meta") in devices:
            devices.remove(torch.device("meta"))
            assign = True
        if len(devices) == 0:
            devices.add(dist.distributed_c10d._get_pg_default_device())
        elif len(devices) > 1:
            raise ValueError("Multiple devices found")

        if info.broadcast_from_rank0:
            _broadcast_state_dict(
                state_dict,
                local_state_dict,
                device=devices.pop(),
                strict=info.strict,
                cpu_offload=info.cpu_offload,
            )
        elif info.full_state_dict:
            _distribute_state_dict(state_dict, local_state_dict, device=devices.pop())
        state_dict.update(local_state_dict)

    with info.fsdp_context():
        return cast(
            _IncompatibleKeys,
            _state_dict_fn(model, "load_state_dict")(
                state_dict=state_dict, strict=info.strict, assign=assign
            ),
        )