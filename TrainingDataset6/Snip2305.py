def open_command(arg):
    if find_executable('xdg-open'):
        return 'xdg-open ' + arg
    return 'open ' + arg