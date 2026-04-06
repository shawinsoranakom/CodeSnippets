def _get_brew_commands(brew_path_prefix):
    """To get brew default commands on local environment"""
    brew_cmd_path = brew_path_prefix + BREW_CMD_PATH

    return [name[:-3] for name in os.listdir(brew_cmd_path)
            if name.endswith(('.rb', '.sh'))]