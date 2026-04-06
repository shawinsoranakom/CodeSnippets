def match(command):
    return ('push' in command.script_parts
            and 'git push --set-upstream' in command.output)