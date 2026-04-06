def get_new_command(command):
    broken_cmd = re.findall(r'Error: unknown command "([^"]*)" for "git-lfs"', command.output)[0]
    matched = get_all_matched_commands(command.output, ['Did you mean', ' for usage.'])
    return replace_command(command, broken_cmd, matched)