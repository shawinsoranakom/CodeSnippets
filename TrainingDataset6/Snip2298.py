def archlinux_env():
    if utils.which('yay'):
        pacman = 'yay'
    elif utils.which('pikaur'):
        pacman = 'pikaur'
    elif utils.which('yaourt'):
        pacman = 'yaourt'
    elif utils.which('pacman'):
        pacman = 'sudo pacman'
    else:
        return False, None

    enabled_by_default = utils.which('pkgfile')

    return enabled_by_default, pacman