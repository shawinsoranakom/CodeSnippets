def match(command):
    return (command.script_parts[1] in ['uninstall', 'rm', 'remove']
            and "brew uninstall --force" in command.output)