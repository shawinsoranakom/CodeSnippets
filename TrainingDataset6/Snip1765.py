def _get_user_dir_path(self):
        """Returns Path object representing the user config resource"""
        xdg_config_home = os.environ.get('XDG_CONFIG_HOME', '~/.config')
        user_dir = Path(xdg_config_home, 'thefuck').expanduser()
        legacy_user_dir = Path('~', '.thefuck').expanduser()

        # For backward compatibility use legacy '~/.thefuck' if it exists:
        if legacy_user_dir.is_dir():
            warn(u'Config path {} is deprecated. Please move to {}'.format(
                legacy_user_dir, user_dir))
            return legacy_user_dir
        else:
            return user_dir