def _get_param_key_to_param(
    optim: torch.optim.Optimizer,
    model: nn.Module | None = None,
    is_named_optimizer: bool = False,
    param_to_fqns: dict[nn.Parameter, list[str]] | None = None,
    flat_param_to_fqn: dict[FlatParameter, str] | None = None,
) -> dict[int | str, nn.Parameter]:
    """
    Constructs a mapping from parameter keys to parameters. For the regular
    optimizers, the keys are parameter IDs. For NamedOptimizer, the keys
    are FQNs. This API may be used both for models with ``FlatParameter`` s and
    without.
    """
    clean_fqn_to_curr_fqn: dict[str, str] = {}
    if is_named_optimizer:
        if param_to_fqns is None or flat_param_to_fqn is None:
            raise AssertionError(
                "The optimizer is a NamedOptimizer, `param_to_fqns` must not be None."
            )
        if model is None:
            raise AssertionError(f"Expected model to be not None, got {model}")
        for key, _ in _named_parameters_with_duplicates(model):
            clean_fqn_to_curr_fqn[clean_tensor_name(key)] = key

    param_key_to_param: dict[str | int, nn.Parameter] = {}
    pid = 0
    for param_group in optim.param_groups:
        if is_named_optimizer:
            for param in param_group["params"]:
                if flat_param_to_fqn is None:
                    raise AssertionError(
                        f"Expected flat_param_to_fqn to be not None, got {flat_param_to_fqn}"
                    )
                if param in flat_param_to_fqn:
                    # FlatParameter case
                    key = flat_param_to_fqn[param]
                else:
                    if param_to_fqns is None:
                        raise AssertionError(
                            f"Expected param_to_fqns to be not None, got {param_to_fqns}"
                        )
                    # use_orig_params case
                    if len(param_to_fqns[param]) != 1:
                        raise AssertionError(
                            f"Expected len(param_to_fqns[param]) == 1, got {len(param_to_fqns[param])}"
                        )
                    key = param_to_fqns[param][0]
                try:
                    key = clean_fqn_to_curr_fqn[key]
                except KeyError as e:
                    raise KeyError(
                        f"Can't find {key} from {list(clean_fqn_to_curr_fqn.keys())}."
                    ) from e
                param_key_to_param[key] = param
        else:
            for param in param_group["params"]:
                param_key_to_param[pid] = param
                pid += 1

    return param_key_to_param