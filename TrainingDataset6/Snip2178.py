def _get_command_name(command):
    found = re.findall(r'sudo: (.*): command not found', command.output)
    if found:
        return found[0]