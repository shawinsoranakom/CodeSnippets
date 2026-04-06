def match(command):
    return ('update' in command.script
            and "Error: This command updates brew itself" in command.output
            and "Use `brew upgrade" in command.output)