def match(command):
    port = _get_used_port(command)
    return port and _get_pid_by_port(port)