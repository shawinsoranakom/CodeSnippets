def get_new_command(command):
    old_command = command.script_parts[0]

    # One from history:
    already_used = get_closest(
        old_command, _get_used_executables(command),
        fallback_to_first=False)
    if already_used:
        new_cmds = [already_used]
    else:
        new_cmds = []

    # Other from all executables:
    new_cmds += [cmd for cmd in get_close_matches(old_command,
                                                  get_all_executables())
                 if cmd not in new_cmds]

    return [command.script.replace(old_command, cmd, 1) for cmd in new_cmds]