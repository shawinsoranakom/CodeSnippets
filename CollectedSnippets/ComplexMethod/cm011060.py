def _get_param_id_to_param_from_optim_input(
    model: nn.Module,
    optim_input: list[dict[str, Any]] | Iterable[nn.Parameter] | None = None,
) -> dict[int, nn.Parameter]:
    """
    Constructs a mapping from parameter IDs to parameters. This may be used
    both for models with ``FlatParameter`` s and without.

    NOTE: This method is only preserved for backward compatibility. The method
    :meth:`_get_param_key_to_param` is the preferred code path that does not
    rely on ``optim_input``.

    NOTE: We critically assume that, whether the optimizer input is a list of
    parameters or a list of parameter groups, :class:`torch.optim.Optimizer`
    enumerates the parameter IDs in order. In other words, for a parameter list
    input, the parameter IDs should be in that list order, and for a parameter
    groups input, the parameter IDs should be in order within each parameter
    group and in order across parameter groups.

    Args:
        model (nn.Module): Model whose parameters are passed into the
            optimizer.
        optim_input (Optional[Union[List[Dict[str, Any]],
        Iterable[nn.Parameter]]]): Input passed into the optimizer
            representing either a :class:`list` of parameter groups or an
            iterable of parameters; if ``None``, then this method assumes the
            input was ``model.parameters()``. (Default: ``None``)

    Returns:
        List[nn.Parameter]: Mapping from parameter IDs to parameters,
        where the parameter ID is implicitly the index in the :class:`list`.
    """
    # Assume the standard case of passing `model.parameters()` to the optimizer
    # if `optim_input` is not specified
    if optim_input is None:
        return dict(enumerate(model.parameters()))
    try:
        # pyrefly: ignore [redundant-cast]
        params = cast(list[nn.Parameter], list(optim_input))
    except TypeError as e:
        raise TypeError(
            "Optimizer input should be an iterable of Tensors or dicts, "
            f"but got {optim_input}"
        ) from e
    if len(params) == 0:
        raise ValueError("Optimizer input should not be empty")

    # Check if the optimizer input represents tensors or parameter groups
    all_tensors = True
    all_dicts = True
    for param in params:
        all_tensors &= isinstance(param, torch.Tensor)
        all_dicts &= isinstance(param, dict)
    if not all_tensors and not all_dicts:
        raise TypeError("Optimizer input should be an iterable of Tensors or dicts")
    if all_tensors:
        return dict(enumerate(params))
    if not all_dicts:
        raise AssertionError(f"Expected all_dicts to be True, got {all_dicts}")
    param_id_to_param: list[nn.Parameter] = []
    for param_group in params:
        has_params_key = "params" in param_group  # type: ignore[operator]
        if not has_params_key:
            raise AssertionError(
                'A parameter group should map "params" to a list of the parameters in the group'
            )
        # Implicitly map `flat_param_id` (current length of the list) to
        # `param`
        param_id_to_param.extend(param_group["params"])  # type: ignore[index]
    return dict(enumerate(param_id_to_param))