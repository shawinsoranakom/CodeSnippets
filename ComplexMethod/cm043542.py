def _build_command_choice_map(argument_parser: ArgumentParser) -> dict:
    """Build the choice map for a command."""
    choice_map: dict = {}
    for action in argument_parser._actions:  # pylint: disable=protected-access
        if action.help == SUPPRESS:
            continue
        if len(action.option_strings) == 1:
            long_name = action.option_strings[0]
            short_name = ""
        elif len(action.option_strings) == 2:
            short_name = action.option_strings[0]
            long_name = action.option_strings[1]
        else:
            raise AttributeError(f"Invalid argument_parser: {argument_parser}")

        if hasattr(action, "choices") and action.choices:
            choice_map[long_name] = {str(c): {} for c in action.choices}
        else:
            choice_map[long_name] = {}

        if short_name and long_name:
            choice_map[short_name] = long_name

    return choice_map