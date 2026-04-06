def get_new_command(command):
    packages = get_pkgfile(command.script)

    formatme = shell.and_('{} -S {}', '{}')
    return [formatme.format(pacman, package, command.script)
            for package in packages]