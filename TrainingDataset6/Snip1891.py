def get_new_command(command):
    match = re.findall(r"'conda ([^']*)'", command.output)
    broken_cmd = match[0]
    correct_cmd = match[1]
    return replace_command(command, broken_cmd, [correct_cmd])