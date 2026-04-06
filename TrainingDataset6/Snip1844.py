def get_new_command(command):
    mistake = re.search(INVALID_CHOICE, command.output).group(0)
    options = re.findall(OPTIONS, command.output, flags=re.MULTILINE)
    return [replace_argument(command.script, mistake, o) for o in options]