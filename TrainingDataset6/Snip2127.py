def _get_destination(command):
    for pattern in patterns:
        found = re.findall(pattern, command.output)
        if found:
            if found[0] in command.script_parts:
                return found[0]