def _check_ignored_states(
    ignored_states: list[Any], passed_as_ignored_states: bool
) -> None:
    """
    Check that the ignored states are uniformly parameters or uniformly modules.

    We may remove this check in the future if we permit mixing.
    """
    if len(ignored_states) == 0:
        return
    if passed_as_ignored_states:
        all_params = all(isinstance(state, nn.Parameter) for state in ignored_states)
        all_modules = all(isinstance(state, nn.Module) for state in ignored_states)
        if not all_params and not all_modules:
            # Sort for consistent ordering for unit test regex matching
            sorted_types = sorted({type(state) for state in ignored_states}, key=repr)
            raise ValueError(
                "ignored_states expects all nn.Parameter or all nn.Module list "
                f"elements but got types {sorted_types}"
            )
    else:
        if not all(isinstance(state, nn.Module) for state in ignored_states):
            sorted_types = sorted({type(state) for state in ignored_states}, key=repr)
            raise ValueError(
                "ignored_modules expects nn.Module list elements but got "
                f"types {sorted_types}"
            )