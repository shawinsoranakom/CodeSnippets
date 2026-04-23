def _get_linux_desktop_environment(env, logger):
    """
    https://chromium.googlesource.com/chromium/src/+/refs/heads/main/base/nix/xdg_util.cc
    GetDesktopEnvironment
    """
    xdg_current_desktop = env.get('XDG_CURRENT_DESKTOP', None)
    desktop_session = env.get('DESKTOP_SESSION', '')
    if xdg_current_desktop is not None:
        for part in map(str.strip, xdg_current_desktop.split(':')):
            if part == 'Unity':
                if 'gnome-fallback' in desktop_session:
                    return _LinuxDesktopEnvironment.GNOME
                else:
                    return _LinuxDesktopEnvironment.UNITY
            elif part == 'Deepin':
                return _LinuxDesktopEnvironment.DEEPIN
            elif part == 'GNOME':
                return _LinuxDesktopEnvironment.GNOME
            elif part == 'X-Cinnamon':
                return _LinuxDesktopEnvironment.CINNAMON
            elif part == 'KDE':
                kde_version = env.get('KDE_SESSION_VERSION', None)
                if kde_version == '5':
                    return _LinuxDesktopEnvironment.KDE5
                elif kde_version == '6':
                    return _LinuxDesktopEnvironment.KDE6
                elif kde_version == '4':
                    return _LinuxDesktopEnvironment.KDE4
                else:
                    logger.info(f'unknown KDE version: "{kde_version}". Assuming KDE4')
                    return _LinuxDesktopEnvironment.KDE4
            elif part == 'Pantheon':
                return _LinuxDesktopEnvironment.PANTHEON
            elif part == 'XFCE':
                return _LinuxDesktopEnvironment.XFCE
            elif part == 'UKUI':
                return _LinuxDesktopEnvironment.UKUI
            elif part == 'LXQt':
                return _LinuxDesktopEnvironment.LXQT
        logger.debug(f'XDG_CURRENT_DESKTOP is set to an unknown value: "{xdg_current_desktop}"')

    if desktop_session == 'deepin':
        return _LinuxDesktopEnvironment.DEEPIN
    elif desktop_session in ('mate', 'gnome'):
        return _LinuxDesktopEnvironment.GNOME
    elif desktop_session in ('kde4', 'kde-plasma'):
        return _LinuxDesktopEnvironment.KDE4
    elif desktop_session == 'kde':
        if 'KDE_SESSION_VERSION' in env:
            return _LinuxDesktopEnvironment.KDE4
        else:
            return _LinuxDesktopEnvironment.KDE3
    elif 'xfce' in desktop_session or desktop_session == 'xubuntu':
        return _LinuxDesktopEnvironment.XFCE
    elif desktop_session == 'ukui':
        return _LinuxDesktopEnvironment.UKUI
    else:
        logger.debug(f'DESKTOP_SESSION is set to an unknown value: "{desktop_session}"')

    if 'GNOME_DESKTOP_SESSION_ID' in env:
        return _LinuxDesktopEnvironment.GNOME
    elif 'KDE_FULL_SESSION' in env:
        if 'KDE_SESSION_VERSION' in env:
            return _LinuxDesktopEnvironment.KDE4
        else:
            return _LinuxDesktopEnvironment.KDE3

    return _LinuxDesktopEnvironment.OTHER