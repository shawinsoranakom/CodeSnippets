def match(command):
    if 'not found' in command.output or 'not installed' in command.output:
        executable = _get_executable(command)
        return not which(executable) and get_package(executable)
    else:
        return False