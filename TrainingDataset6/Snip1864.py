def _brew_commands():
    brew_path_prefix = get_brew_path_prefix()
    if brew_path_prefix:
        try:
            return (_get_brew_commands(brew_path_prefix)
                    + _get_brew_tap_specific_commands(brew_path_prefix))
        except OSError:
            pass

    # Failback commands for testing (Based on Homebrew 0.9.5)
    return ['info', 'home', 'options', 'install', 'uninstall',
            'search', 'list', 'update', 'upgrade', 'pin', 'unpin',
            'doctor', 'create', 'edit', 'cask']