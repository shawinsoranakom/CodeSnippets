def create_page_profile_message(
    commands: List[Command],
    exec_time: int,
    prep_time: int,
    uncaught_exception: Optional[str] = None,
) -> ForwardMsg:
    """Create and return the full PageProfile ForwardMsg."""
    msg = ForwardMsg()
    msg.page_profile.commands.extend(commands)
    msg.page_profile.exec_time = exec_time
    msg.page_profile.prep_time = prep_time

    msg.page_profile.headless = config.get_option("server.headless")

    # Collect all config options that have been manually set
    config_options: Set[str] = set()
    if config._config_options:
        for option_name in config._config_options.keys():
            if not config.is_manually_set(option_name):
                # We only care about manually defined options
                continue

            config_option = config._config_options[option_name]
            if config_option.is_default:
                option_name = f"{option_name}:default"
            config_options.add(option_name)

    msg.page_profile.config.extend(config_options)

    # Check the predefined set of modules for attribution
    attributions: Set[str] = {
        attribution
        for attribution in _ATTRIBUTIONS_TO_CHECK
        if attribution in sys.modules
    }

    msg.page_profile.os = str(sys.platform)
    msg.page_profile.timezone = str(time.tzname)
    msg.page_profile.attributions.extend(attributions)

    if uncaught_exception:
        msg.page_profile.uncaught_exception = uncaught_exception

    return msg