def _get_shell_from_env():
    name = os.environ.get('TF_SHELL')

    if name in shells:
        return shells[name]()