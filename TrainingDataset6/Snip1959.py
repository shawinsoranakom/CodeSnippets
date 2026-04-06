def get_new_command(command):
    missing_file = re.findall(
        r"error: pathspec '([^']*)' "
        r"did not match any file\(s\) known to git", command.output)[0]
    closest_branch = utils.get_closest(missing_file, get_branches(),
                                       fallback_to_first=False)

    new_commands = []

    if closest_branch:
        new_commands.append(replace_argument(command.script, missing_file, closest_branch))
    if command.script_parts[1] == 'checkout':
        new_commands.append(replace_argument(command.script, 'checkout', 'checkout -b'))

    if not new_commands:
        new_commands.append(shell.and_('git branch {}', '{}').format(
            missing_file, command.script))

    return new_commands