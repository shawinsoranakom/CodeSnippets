def _set_development_mode() -> None:
    development.is_development_mode = get_option("global.developmentMode")