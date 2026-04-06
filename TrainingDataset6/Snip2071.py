def match(command):
    return (command.output.endswith("hard link not allowed for directory") and
            command.script_parts[0] == 'ln')