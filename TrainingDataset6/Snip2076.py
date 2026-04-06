def match(command):
    if re.search(help_regex, command.output, re.I) is not None:
        return True

    if '--help' in command.output:
        return True

    return False