def _rekey_sharded_optim_state_dict(
    sharded_osd: dict[str, Any],
    model: nn.Module,
    optim: torch.optim.Optimizer,
    optim_input: list[dict[str, Any]] | Iterable[nn.Parameter] | None,
    using_optim_input: bool,
    is_named_optimizer: bool = False,
) -> dict[str, Any]:
    """
    Rekeys the optimizer state dict from unflattened parameter names to flat
    parameter IDs according to the calling rank's ``optim``, which may be
    different across ranks. In particular, the unflattened parameter names are
    represented as :class:`_OptimStateKey` s.
    """
    param_to_fqns = _get_param_to_fqns(model)
    flat_param_to_fqn = _get_flat_param_to_fqn(model)
    param_to_param_key: dict[nn.Parameter, int | str] = cast(
        dict[nn.Parameter, int | str],
        (
            _get_param_to_param_id_from_optim_input(model, optim_input)
            if using_optim_input
            else _get_param_to_param_key(
                optim, model, is_named_optimizer, param_to_fqns, flat_param_to_fqn
            )
        ),
    )
    # All parameter keys in `param_to_param_key` should be in
    # `param_to_fqns` -- strict inequality follows when not all parameters are
    # passed to the optimizer
    if len(param_to_param_key) > len(param_to_fqns):
        raise AssertionError(
            f"Expected len(param_to_param_key) <= len(param_to_fqns), got {len(param_to_param_key)} > {len(param_to_fqns)}"
        )

    unflat_param_names_to_flat_param_key: dict[
        tuple[str, ...], int | str
    ] = {}  # for "state"
    unflat_param_name_to_flat_param_key: dict[str, int | str] = {}  # for "param_groups"
    for param, unflat_param_names in param_to_fqns.items():
        if param not in param_to_param_key:
            # This parameter was not passed to the optimizer
            continue
        flat_param_key = param_to_param_key[param]
        unflat_param_names_to_flat_param_key[tuple(unflat_param_names)] = flat_param_key
        for unflat_param_name in unflat_param_names:
            unflat_param_name_to_flat_param_key[unflat_param_name] = flat_param_key

    sharded_osd_state = sharded_osd["state"]
    rekeyed_osd_state: dict[str | int, Any] = {}
    for key, param_state in sharded_osd_state.items():
        if isinstance(key, str):
            rekeyed_osd_state[key] = param_state
            continue
        flat_param_key = unflat_param_names_to_flat_param_key.get(
            key.unflat_param_names, key.unflat_param_names
        )

        rekeyed_osd_state[flat_param_key] = param_state

    # Only process param_groups if it exists in sharded_osd
    if "param_groups" in sharded_osd:
        rekeyed_osd_param_groups: list[dict[str, Any]] = []
        for unflat_param_group in sharded_osd["param_groups"]:
            flat_param_group = copy.deepcopy(unflat_param_group)
            flat_param_keys = sorted(
                {
                    unflat_param_name_to_flat_param_key[unflat_param_name]
                    for unflat_param_name in unflat_param_group["params"]
                }
            )
            flat_param_group["params"] = flat_param_keys
            rekeyed_osd_param_groups.append(flat_param_group)
        return {"state": rekeyed_osd_state, "param_groups": rekeyed_osd_param_groups}
    else:
        return {"state": rekeyed_osd_state}