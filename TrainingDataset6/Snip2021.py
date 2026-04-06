def match(command):
    return (' rm ' in command.script and
            'error: the following file has changes staged in the index' in command.output and
            'use --cached to keep the file, or -f to force removal' in command.output)