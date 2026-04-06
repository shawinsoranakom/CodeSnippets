def match(command):
    return 'apt list --upgradable' in command.output