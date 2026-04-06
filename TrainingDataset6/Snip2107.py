def match(command):
    return (any(part.startswith('ru') for part in command.script_parts)
            and 'npm ERR! missing script: ' in command.output)