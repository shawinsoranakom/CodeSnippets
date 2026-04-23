def _get_brew_tap_specific_commands(brew_path_prefix):
    """To get tap's specific commands
    https://github.com/Homebrew/homebrew/blob/master/Library/brew.rb#L115"""
    commands = []
    brew_taps_path = brew_path_prefix + TAP_PATH

    for user in _get_directory_names_only(brew_taps_path):
        taps = _get_directory_names_only(brew_taps_path + '/%s' % user)

        # Brew Taps's naming rule
        # https://github.com/Homebrew/homebrew/blob/master/share/doc/homebrew/brew-tap.md#naming-conventions-and-limitations
        taps = (tap for tap in taps if tap.startswith('homebrew-'))
        for tap in taps:
            tap_cmd_path = brew_taps_path + TAP_CMD_PATH % (user, tap)

            if os.path.isdir(tap_cmd_path):
                commands += (name.replace('brew-', '').replace('.rb', '')
                             for name in os.listdir(tap_cmd_path)
                             if _is_brew_tap_cmd_naming(name))

    return commands