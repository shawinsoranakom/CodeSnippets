def _get_unknown_command(command):
    return re.findall(r'Unknown command (.*)$', command.output)[0]