def remove_argument(parser: ArgumentParser, argument_name: str) -> list[str | None]:
    """Remove an argument from an ArgumentParser."""
    groups_w_arg = []

    # remove the argument from the parser
    for action in parser._actions:  # pylint: disable=protected-access
        opts = action.option_strings
        if (opts and opts[0] == argument_name) or action.dest == argument_name:
            parser._remove_action(action)  # pylint: disable=protected-access
            break

    # remove from all groups
    for action_group in parser._action_groups:  # pylint: disable=protected-access
        for action in action_group._group_actions:  # pylint: disable=protected-access
            opts = action.option_strings
            if (opts and opts[0] == argument_name) or action.dest == argument_name:
                action_group._group_actions.remove(  # pylint: disable=protected-access
                    action
                )
                groups_w_arg.append(action_group.title)

    # remove from _action_groups dict
    parser._option_string_actions.pop(  # pylint: disable=protected-access
        f"--{argument_name}", None
    )

    return groups_w_arg