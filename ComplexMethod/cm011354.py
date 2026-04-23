def _get_optim_state_dict(
    model: nn.Module,
    optimizers: tuple[torch.optim.Optimizer, ...],
    info: _StateDictInfo,
) -> OptimizerStateType:
    if not info.handle_optim:
        return {}

    optim_state_dict: OptimizerStateType = {_STATE: {}, _PG: []}
    for optim in optimizers:
        _init_optim_state(optim)
        osd = _state_dict_fn(optim, "state_dict")()
        if info.fsdp_modules:
            with info.fsdp_context():
                osd = FSDP.optim_state_dict(model, optim, osd)

            # We need to specially handle FlatParameter FSDP as
            # FlatParameter FSDP converts the FQNs.
            # There are no easy ways to do this conversion systematically.
            # We can only use a string replacement without correctness check.
            if not osd:
                continue
            for k in list(osd[_STATE].keys()):
                if "_orig_mod" in k:
                    osd[_STATE][k.replace("_orig_mod.", "")] = osd[_STATE].pop(k)
            for g in osd[_PG]:
                params = [k.replace("_orig_mod.", "") for k in g[_PARAMS]]
                g[_PARAMS] = params
        else:
            params = list(chain.from_iterable(g[_PARAMS] for g in optim.param_groups))
            param_pid_mapping = dict(zip(params, range(len(params))))
            fqn_pid_mapping = {}
            for key, param in model.named_parameters():
                fqns = _get_fqns(model, key)
                if len(fqns) != 1:
                    raise AssertionError(
                        f"Expected 1 FQN for key '{key}', got {len(fqns)}"
                    )
                fqn = next(iter(fqns))
                if param not in param_pid_mapping:
                    continue
                # pyrefly: ignore [bad-index]
                pid = param_pid_mapping[param]
                fqn_pid_mapping[fqn] = pid
                # pyrefly: ignore [unsupported-operation]
                fqn_pid_mapping[pid] = fqn

            # Only convert top-level parameter IDs to FQNs, preserve nested key types
            for key in list(osd[_STATE].keys()):
                fqn = fqn_pid_mapping[key]
                # Move the entire state dict value (which may contain nested integer keys)
                # without modifying its internal structure
                osd[_STATE][fqn] = osd[_STATE].pop(key)

            for group in osd[_PG]:
                group[_PARAMS] = [fqn_pid_mapping[pid] for pid in group[_PARAMS]]

        if not osd:
            continue

        cast(DictValueType, optim_state_dict[_STATE]).update(osd[_STATE])
        cast(ListDictValueType, optim_state_dict[_PG]).extend(osd[_PG])

    if info.flatten_optimizer_state_dict:
        optim_state_dict = cast(
            OptimizerStateType, _flatten_optim_state_dict(optim_state_dict)
        )

    return _maybe_full_or_cpu_state_dict(optim_state_dict, info)