def match(command):
    return (' rm ' in command.script
            and "fatal: not removing '" in command.output
            and "' recursively without -r" in command.output)