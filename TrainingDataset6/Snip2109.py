def match(command):
    return ('Usage: npm <command>' in command.output
            and not any(part.startswith('ru') for part in command.script_parts)
            and command.script_parts[1] in get_scripts())