def match(command):
    return ('bisect' in command.script_parts and
            'usage: git bisect' in command.output)