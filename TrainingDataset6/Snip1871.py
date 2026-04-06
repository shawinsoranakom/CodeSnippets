def match(command):
    return ('no such subcommand' in command.output.lower()
            and 'Did you mean' in command.output)