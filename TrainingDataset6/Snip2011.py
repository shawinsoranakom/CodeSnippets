def match(command):
    return (
        {'rebase', '--continue'}.issubset(command.script_parts) and
        'No changes - did you forget to use \'git add\'?' in command.output
    )