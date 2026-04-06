def match(command):
    return ('fatal: Not a git repository' in command.output
            and "Stopping at filesystem boundary (GIT_DISCOVERY_ACROSS_FILESYSTEM not set)." in command.output)