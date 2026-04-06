def get_new_command(command):
    interface = command.output.split(' ')[0][:-1]
    possible_interfaces = _get_possible_interfaces()
    return replace_command(command, interface, possible_interfaces)