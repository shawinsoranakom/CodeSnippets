def _map_param_key_to_optim_keys(
    optim_state_dict: dict[str, Any],
    group: dist.ProcessGroup | None,
    param_key_to_param: dict[int | str, nn.Parameter],
    param_to_fqns: dict[nn.Parameter, list[str]],
    fqn_to_fsdp_param_info: dict[str, FSDPParamInfo],
    merge_keys: bool = False,
) -> tuple[list[_OptimStateKey], dict[_OptimStateKey, int | str]]:
    """
    Construct the local mapping between the ``_OptimStateKey`` and parameter keys
    and all the ``_OptimStateKey`` across ranks. If ``merge_keys`` is False, rank0
    must contain all the ``_OptimStateKey``, an exception will be raised otherwise.
    Note that ``merge_keys`` should equal to ``use_orig_params``.
    """
    rank = dist.get_rank(group)
    optim_state_key_to_param_key: dict[_OptimStateKey, int | str] = {}  # local
    all_optim_state_keys: list[_OptimStateKey] = []

    for param_key, param in param_key_to_param.items():
        # Do not include parameters without state to avoid empty mappings
        # just like in normal `torch.optim.Optimizer.state_dict()`
        if param_key not in optim_state_dict["state"]:
            continue
        fqns = param_to_fqns[param]
        is_fsdp_managed = isinstance(param, FlatParameter)
        if is_fsdp_managed:
            if fqns[0] not in fqn_to_fsdp_param_info:
                raise AssertionError(
                    f"Expected {fqns[0]} to be in fqn_to_fsdp_param_info, got keys: {list(fqn_to_fsdp_param_info.keys())}"
                )
        is_fsdp_managed = fqns[0] in fqn_to_fsdp_param_info
        optim_state_key = _OptimStateKey(
            unflat_param_names=tuple(fqns),
            is_fsdp_managed=is_fsdp_managed,
        )
        if rank == 0 or merge_keys:
            all_optim_state_keys.append(optim_state_key)
        optim_state_key_to_param_key[optim_state_key] = param_key

    if merge_keys:
        all_keys: list[list[_OptimStateKey]] = [
            [] for _ in range(dist.get_world_size(group))
        ]
        dist.all_gather_object(all_keys, all_optim_state_keys, group=group)
        merge_all_optim_state_keys = [*chain.from_iterable(all_keys)]
        all_optim_state_keys = sorted(set(merge_all_optim_state_keys))
    else:
        key_obj_list: list[list[_OptimStateKey] | None] = (
            [all_optim_state_keys] if rank == 0 else [None]
        )
        dist.broadcast_object_list(key_obj_list, src=0, group=group)
        if key_obj_list[0] is None:
            raise AssertionError(
                f"Expected key_obj_list[0] to be not None, got {key_obj_list[0]}"
            )
        all_optim_state_keys = key_obj_list[0]
        _check_missing_keys_on_rank(
            all_optim_state_keys,
            optim_state_key_to_param_key,
            param_key_to_param,
            group,
        )

    return all_optim_state_keys, optim_state_key_to_param_key