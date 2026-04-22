def configurator_options(func):
    """Decorator that adds config param keys to click dynamically."""
    for _, value in reversed(_config._config_options_template.items()):
        parsed_parameter = _convert_config_option_to_click_option(value)
        config_option = click.option(
            parsed_parameter["option"],
            parsed_parameter["param"],
            help=parsed_parameter["description"],
            type=parsed_parameter["type"],
            show_envvar=True,
            envvar=parsed_parameter["envvar"],
        )
        func = config_option(func)
    return func