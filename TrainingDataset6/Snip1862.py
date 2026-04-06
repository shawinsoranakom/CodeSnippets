def _is_brew_tap_cmd_naming(name):
    return name.startswith('brew-') and name.endswith('.rb')