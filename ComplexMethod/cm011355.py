def _split_optim_state_dict(
    model: nn.Module,
    optim: torch.optim.Optimizer,
    optim_state_dict: OptimizerStateType,
    info: _StateDictInfo,
) -> OptimizerStateType:
    """
    Extract the corresponding optim state_dict from ``optim_state_dict`` for
    ``optim`` and return the result optim state_dict.

    Args:
        model (nn.Module): the root model.
        optim (torch.optim.Optimizer): the optimizer.
        optim_state_dict (Dict[str, ValueType]): the superset optim state_dict that
            contains the optim state_dict of ``optim``.
        info (_StateDictInfo): state dict information.

    Returns:
        The optim state_dict of ``optim``.
    """

    state: DictValueType = {}
    pg_state: ListDictValueType = []
    return_osd: OptimizerStateType = {_STATE: state, _PG: pg_state}
    pg_mapping: dict[int, int] = {}

    if all(isinstance(k, int) for k in cast(DictValueType, optim_state_dict[_STATE])):
        return optim_state_dict

    for param_group in optim.param_groups:
        pg_state.append({_PARAMS: []})
        for param in param_group[_PARAMS]:
            for fqn in info.fqn_param_mapping[param]:
                if fqn in info.shared_params_mapping:
                    in_params = False
                    for loaded_param_group in cast(
                        ListDictValueType, optim_state_dict[_PG]
                    ):
                        if fqn in cast(list[str], loaded_param_group[_PARAMS]):
                            in_params = True
                            break
                else:
                    in_params = True
                if not in_params:
                    continue

                params = pg_state[-1][_PARAMS]
                if not isinstance(params, list):
                    raise AssertionError(f"Expected list, got {type(params)}")
                params.append(fqn)
                if param.requires_grad:
                    if fqn in cast(DictValueType, optim_state_dict[_STATE]):
                        state[fqn] = cast(DictValueType, optim_state_dict[_STATE])[fqn]
                    elif info.strict:
                        raise RuntimeError(
                            f"Missing optimizer state for parameter '{fqn}' in checkpoint. "
                            "The parameter requires gradients but has no saved optimizer state. "
                            "To load anyway, use StateDictOptions(strict=False)."
                        )
                for loaded_param_group in cast(
                    ListDictValueType, optim_state_dict[_PG]
                ):
                    if fqn in cast(list[str], loaded_param_group[_PARAMS]):
                        pg_mapping[id(loaded_param_group)] = len(return_osd[_PG]) - 1

        if len(param_group[_PARAMS]) == 0:
            # Param_group with empty params.
            ret = []
            for loaded_param_group in cast(ListDictValueType, optim_state_dict[_PG]):
                if len(cast(list[str], loaded_param_group[_PARAMS])) == 0:
                    ret.append(loaded_param_group)
            if len(ret) != 1:
                raise ValueError(
                    "There are param groups that have zero parameters. "
                    "In such a case, DSD only support exactly one param group "
                    "with zero parameters."
                    "But the loaded state_dict has zero or more than one param groups "
                    "that have zero parameters."
                )
            if len(optim_state_dict[_PG]) != len(optim.param_groups):
                raise ValueError(
                    "When there is a parameter group that has zero parameters, "
                    "multiple optimizers are not supported."
                )
            pg_mapping[id(loaded_param_group)] = len(return_osd[_PG]) - 1

    for param_group in cast(ListDictValueType, optim_state_dict[_PG]):
        pg_idx = pg_mapping.get(id(param_group), -1)
        if pg_idx == -1:
            continue

        for key, value in param_group.items():
            if key == _PARAMS:
                continue
            # TODO: check if value is the same if exists.
            pg_state[pg_idx][key] = value

    return return_osd