def match(command):
    # catches "git branch list" in place of "git branch"
    return (command.script_parts
            and command.script_parts[1:] == 'branch list'.split())