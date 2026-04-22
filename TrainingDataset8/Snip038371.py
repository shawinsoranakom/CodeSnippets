def _install_config_watchers(flag_options: Dict[str, Any]) -> None:
    def on_config_changed(_path):
        load_config_options(flag_options)

    for filename in CONFIG_FILENAMES:
        if os.path.exists(filename):
            watch_file(filename, on_config_changed)