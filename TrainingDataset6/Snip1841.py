def match(command):
    return command.script == "apt list --upgradable" and len(command.output.strip().split('\n')) > 1