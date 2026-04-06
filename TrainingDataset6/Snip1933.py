def match(command):
    if 'EDITOR' not in os.environ:
        return False

    return _search(command.output)