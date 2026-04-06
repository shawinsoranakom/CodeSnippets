def match(command):
    return 'is not a docker command' in command.output or 'Usage:	docker' in command.output