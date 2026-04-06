def invalid_command(command):
    return """No such command: %s. Please use /usr/bin/dnf --help
It could be a DNF plugin command, try: "dnf install 'dnf-command(%s)'"
""" % (command, command)