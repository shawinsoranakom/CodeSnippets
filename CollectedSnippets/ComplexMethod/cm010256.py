def _init_logs(log_file_name=None) -> None:
    global GET_DTRACE_STRUCTURED

    _reset_logs()
    _update_log_state_from_env()

    out = os.environ.get(LOG_OUT_ENV_VAR, None)
    if out is not None:
        log_file_name = out

    # First, reset all known (registered) loggers to NOTSET, so that they
    # respect their parent log level
    for log_qname in log_registry.get_log_qnames():
        # But not the top level torch level: this defaults to WARNING so
        # that our log messages don't leak to the lower levels
        if log_qname == "torch":
            continue
        log = logging.getLogger(log_qname)
        log.setLevel(logging.NOTSET)

    # Now, for all loggers which the user requested to have non-standard
    # logging behavior, modify their log levels
    for log_qname, level in log_state.get_log_level_pairs():
        log = logging.getLogger(log_qname)
        log.setLevel(level)

    # Finally, setup handlers for all registered loggers
    for log_qname in log_registry.get_log_qnames():
        log = logging.getLogger(log_qname)
        _setup_handlers(
            logging.StreamHandler,
            log,
        )

        if log_file_name is not None:
            _setup_handlers(
                lambda: logging.FileHandler(log_file_name),
                log,
            )

    # configure artifact loggers, note: this must happen last
    # since the levels of ancestor loggers are taken into account
    for artifact_log_qname in log_registry.get_artifact_log_qnames():
        log = logging.getLogger(artifact_log_qname)
        configure_artifact_log(log)

    # Setup handler for the special trace_log, with different default
    # configuration
    trace_dir_name = os.environ.get(TRACE_ENV_VAR, None)

    # If TORCH_COMPILE_DEBUG=1 is set but no TORCH_TRACE, automatically use
    # the torch_compile_debug directory for trace logs (to simplify tlparse usage)
    if trace_dir_name is None and os.environ.get("TORCH_COMPILE_DEBUG", "0") == "1":
        import torch._dynamo.config as dynamo_config

        trace_dir_name = os.path.join(dynamo_config.debug_dir_root, "tlparse")

    if dtrace_dir_name := os.environ.get(DTRACE_ENV_VAR, None):
        GET_DTRACE_STRUCTURED = True
        trace_dir_name = dtrace_dir_name

    # This handler may remove itself if trace_dir_name is None and we are not
    # actually in an FB environment.  This allows us to defer actually
    # initializing it until we actually need to log anything.  This is
    # important because JK initializes a C++ singleton, which will pork our
    # process if we subsequently fork.
    global LOG_TRACE_HANDLER
    if LOG_TRACE_HANDLER is None:
        LOG_TRACE_HANDLER = LazyTraceHandler(trace_dir_name)
    # This log is ALWAYS at debug level.  We will additionally test if there
    # are any handlers before deciding to actually call logging on this.  Do
    # not manually call
    trace_log.setLevel(logging.DEBUG)
    trace_log_handler = _track_handler(LOG_TRACE_HANDLER)
    trace_log_handler.setFormatter(TorchLogsFormatter(trace=True))
    trace_log.addHandler(trace_log_handler)