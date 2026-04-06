def match(command):
    return (
        "$: command not found" in command.output
        and re.search(r"^[\s]*\$ [\S]+", command.script) is not None
    )