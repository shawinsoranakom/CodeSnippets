def setup_logging_from_config():
    log_level = get_log_level_from_config()
    setup_logging(log_level)

    if config.is_trace_logging_enabled():
        for name, level in trace_log_levels.items():
            logging.getLogger(name).setLevel(level)
    if config.LS_LOG == constants.LS_LOG_TRACE_INTERNAL:
        for name, level in trace_internal_log_levels.items():
            logging.getLogger(name).setLevel(level)

    raw_logging_override = config.LOG_LEVEL_OVERRIDES
    if raw_logging_override:
        logging_overrides = key_value_pairs_to_dict(raw_logging_override)
        for logger, level_name in logging_overrides.items():
            level = getattr(logging, level_name, None)
            if not level:
                raise ValueError(
                    f"Failed to configure logging overrides ({raw_logging_override}): '{level_name}' is not a valid log level"
                )
            logging.getLogger(logger).setLevel(level)