def get_new_command(command):
    stash_cmd = command.script_parts[2]
    fixed = utils.get_closest(stash_cmd, stash_commands, fallback_to_first=False)

    if fixed is not None:
        return replace_argument(command.script, stash_cmd, fixed)
    else:
        cmd = command.script_parts[:]
        cmd.insert(2, 'save')
        return ' '.join(cmd)