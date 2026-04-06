def match(command):
    return (command.script_parts[1] in ['ln', 'link']
            and "brew link --overwrite --dry-run" in command.output)