def _configure(configuration_details):
    """Adds alias to shell config."""
    path = Path(configuration_details.path).expanduser()
    with path.open('a') as shell_config:
        shell_config.write(u'\n')
        shell_config.write(configuration_details.content)
        shell_config.write(u'\n')