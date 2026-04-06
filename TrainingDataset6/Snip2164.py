def match(command):
    return (command.script_parts
            and {'rm', '/'}.issubset(command.script_parts)
            and '--no-preserve-root' not in command.script
            and '--no-preserve-root' in command.output)