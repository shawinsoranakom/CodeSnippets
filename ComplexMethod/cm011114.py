def _get_ignored_params(
    root_module: torch.nn.Module,
    ignored_modules: set[torch.nn.Module],
    ignored_parameters: Iterable[torch.nn.Parameter] | None = None,
) -> set[torch.nn.Parameter]:
    """
    Return the parameters of the modules in ``ignored_modules`` and the parameters in ``ignored_parameters``.

    :class:`FlatParameter` s are excluded from the result.
    """
    all_ignored_params: set[torch.nn.Parameter] = set()

    params_in_ignored_modules = {
        p for m in ignored_modules for p in m.parameters() if not _is_fsdp_flattened(p)
    }

    all_ignored_params.update(params_in_ignored_modules)

    if ignored_parameters is not None:
        params_in_ignored_parameters = {
            p for p in ignored_parameters if not _is_fsdp_flattened(p)
        }
        all_ignored_params.update(params_in_ignored_parameters)

    # Always include nested FSDP modules' ignored parameters
    for submodule in root_module.modules():
        optional_fsdp_state = _get_module_fsdp_state(submodule)
        if optional_fsdp_state is not None:
            if not hasattr(optional_fsdp_state, "_ignored_params"):
                raise AssertionError(
                    "Expected optional_fsdp_state to have _ignored_params attribute"
                )
            all_ignored_params.update(optional_fsdp_state._ignored_params)

    return all_ignored_params