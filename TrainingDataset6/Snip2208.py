def match(command):
    return 'run `vagrant up`' in command.output.lower()