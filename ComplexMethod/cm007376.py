def _readUserConf():
        xdg_config_home = compat_getenv('XDG_CONFIG_HOME')
        if xdg_config_home:
            userConfFile = os.path.join(xdg_config_home, 'youtube-dl', 'config')
            if not os.path.isfile(userConfFile):
                userConfFile = os.path.join(xdg_config_home, 'youtube-dl.conf')
        else:
            userConfFile = os.path.join(compat_expanduser('~'), '.config', 'youtube-dl', 'config')
            if not os.path.isfile(userConfFile):
                userConfFile = os.path.join(compat_expanduser('~'), '.config', 'youtube-dl.conf')
        userConf = _readOptions(userConfFile, None)

        if userConf is None:
            appdata_dir = compat_getenv('appdata')
            if appdata_dir:
                userConf = _readOptions(
                    os.path.join(appdata_dir, 'youtube-dl', 'config'),
                    default=None)
                if userConf is None:
                    userConf = _readOptions(
                        os.path.join(appdata_dir, 'youtube-dl', 'config.txt'),
                        default=None)

        if userConf is None:
            userConf = _readOptions(
                os.path.join(compat_expanduser('~'), 'youtube-dl.conf'),
                default=None)
        if userConf is None:
            userConf = _readOptions(
                os.path.join(compat_expanduser('~'), 'youtube-dl.conf.txt'),
                default=None)

        if userConf is None:
            userConf = []

        return userConf