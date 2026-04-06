def match(command):
    return (' rebase' in command.script and
            'It seems that there is already a rebase-merge directory' in command.output and
            'I wonder if you are in the middle of another rebase' in command.output)