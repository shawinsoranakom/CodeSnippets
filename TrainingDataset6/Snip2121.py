def match(command):
    return 'not found' in command.output and get_pkgfile(command.script)