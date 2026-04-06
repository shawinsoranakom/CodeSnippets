def match(command):
    return (command.script_parts[0] == 'ln'
            and {'-s', '--symbolic'}.intersection(command.script_parts)
            and 'File exists' in command.output
            and _get_destination(command.script_parts))