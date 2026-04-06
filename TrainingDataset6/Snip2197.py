def get_new_command(command):
    cmd = re.match(r"ambiguous command: (.*), could be: (.*)",
                   command.output)

    old_cmd = cmd.group(1)
    suggestions = [c.strip() for c in cmd.group(2).split(',')]

    return replace_command(command, old_cmd, suggestions)