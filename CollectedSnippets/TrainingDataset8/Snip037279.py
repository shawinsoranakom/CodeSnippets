def get_config_options(
    force_reparse=False, options_from_flags: Optional[Dict[str, Any]] = None
) -> Dict[str, ConfigOption]:
    """Create and return a dict mapping config option names to their values,
    returning a cached dict if possible.

    Config option values are sourced from the following locations. Values
    set in locations further down the list overwrite those set earlier.
      1. default values defined in this file
      2. the global `~/.streamlit/config.toml` file
      3. per-project `$CWD/.streamlit/config.toml` files
      4. environment variables such as `STREAMLIT_SERVER_PORT`
      5. command line flags passed to `streamlit run`

    Parameters
    ----------
    force_reparse : bool
        Force config files to be parsed so that we pick up any changes to them.

    options_from_flags : Optional[Dict[str, any]
        Config options that we received via CLI flag.

    Returns
    ----------
    Dict[str, ConfigOption]
        An ordered dict that maps config option names to their values.
    """
    global _config_options

    if not options_from_flags:
        options_from_flags = {}

    # Avoid grabbing the lock in the case where there's nothing for us to do.
    config_options = _config_options
    if config_options and not force_reparse:
        return config_options

    with _config_lock:
        # Short-circuit if config files were parsed while we were waiting on
        # the lock.
        if _config_options and not force_reparse:
            return _config_options

        old_options = _config_options
        _config_options = copy.deepcopy(_config_options_template)

        # Values set in files later in the CONFIG_FILENAMES list overwrite those
        # set earlier.
        for filename in CONFIG_FILENAMES:
            if not os.path.exists(filename):
                continue

            with open(filename, "r", encoding="utf-8") as input:
                file_contents = input.read()

            _update_config_with_toml(file_contents, filename)

        for opt_name, opt_val in options_from_flags.items():
            _set_option(opt_name, opt_val, _DEFINED_BY_FLAG)

        if old_options and config_util.server_option_changed(
            old_options, _config_options
        ):
            # Import logger locally to prevent circular references.
            from streamlit.logger import get_logger

            LOGGER = get_logger(__name__)
            LOGGER.warning(
                "An update to the [server] config option section was detected."
                " To have these changes be reflected, please restart streamlit."
            )

        _on_config_parsed.send()
        return _config_options