def match(command):
    return ': No such file or directory' in command.output \
        and _get_actual_file(command.script_parts)