def match(command):
    return (
        command.output.startswith('cat: ') and
        os.path.isdir(command.script_parts[1])
    )