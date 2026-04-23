def update_logging_config(*, setting, **kwargs):
    if setting in {"LOGGING", "LOGGING_CONFIG"}:
        configure_logging(settings.LOGGING_CONFIG, settings.LOGGING)