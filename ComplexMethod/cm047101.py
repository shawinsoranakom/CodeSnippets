def init_logger():
    global showwarning  # noqa: PLW0603
    if logging.getLogRecordFactory() is LogRecord:
        return

    logging.setLogRecordFactory(LogRecord)

    logging.captureWarnings(True)
    # must be after `loggin.captureWarnings` so we override *that* instead of
    # the other way around
    showwarning = warnings.showwarning
    warnings.showwarning = showwarning_with_traceback

    # enable deprecation warnings (disabled by default)
    warnings.simplefilter('default', category=DeprecationWarning)
    # https://github.com/urllib3/urllib3/issues/2680
    warnings.filterwarnings('ignore', r'^\'urllib3.contrib.pyopenssl\' module is deprecated.+', category=DeprecationWarning)
    # ignore a bunch of warnings we can't really fix ourselves
    for module in [
        'babel.util', # deprecated parser module, no release yet
        'zeep.loader',# zeep using defusedxml.lxml
        'reportlab.lib.rl_safe_eval',# reportlab importing ABC from collections
        'ofxparse',# ofxparse importing ABC from collections
        'astroid',  # deprecated imp module (fixed in 2.5.1)
        'requests_toolbelt', # importing ABC from collections (fixed in 0.9)
    ]:
        warnings.filterwarnings('ignore', category=DeprecationWarning, module=module)

    # rsjmin triggers this with Python 3.10+ (that warning comes from the C code and has no `module`)
    warnings.filterwarnings('ignore', r'^PyUnicode_FromUnicode\(NULL, size\) is deprecated', category=DeprecationWarning)
    # reportlab<4.0.6 triggers this in Py3.10/3.11
    warnings.filterwarnings('ignore', r'the load_module\(\) method is deprecated', category=DeprecationWarning, module='importlib._bootstrap')
    # the SVG guesser thing always compares str and bytes, ignore it
    warnings.filterwarnings('ignore', category=BytesWarning, module='odoo.tools.image')
    # reportlab does a bunch of bytes/str mixing in a hashmap
    warnings.filterwarnings('ignore', category=BytesWarning, module='reportlab.platypus.paraparser')

    # need to be adapted later but too muchwork for this pr.
    warnings.filterwarnings('ignore', r'^datetime.datetime.utcnow\(\) is deprecated and scheduled for removal in a future version.*', category=DeprecationWarning)

    # pkg_ressouce is used in google-auth < 1.23.0 (removed in https://github.com/googleapis/google-auth-library-python/pull/596)
    # unfortunately, in ubuntu jammy and noble, the google-auth version is 1.5.1
    # starting from noble, the default pkg_ressource version emits a warning on import, triggered when importing
    # google-auth
    warnings.filterwarnings('ignore', r'pkg_resources is deprecated as an API.+', category=DeprecationWarning)
    warnings.filterwarnings('ignore', r'Deprecated call to \`pkg_resources.declare_namespace.+', category=DeprecationWarning)

    # This warning is triggered library only during the python precompilation which does not occur on readonly filesystem
    warnings.filterwarnings("ignore", r'invalid escape sequence', category=DeprecationWarning, module=".*vobject")
    warnings.filterwarnings("ignore", r'invalid escape sequence', category=SyntaxWarning, module=".*vobject")
    from .tools.translate import resetlocale
    resetlocale()

    # create a format for log messages and dates
    format = '%(asctime)s %(pid)s %(levelname)s %(dbname)s %(name)s: %(message)s %(perf_info)s'
    # Normal Handler on stderr
    handler = logging.StreamHandler()

    if tools.config['syslog']:
        # SysLog Handler
        if os.name == 'nt':
            handler = logging.handlers.NTEventLogHandler(f"{release.description} {release.version}")
        elif platform.system() == 'Darwin':
            handler = logging.handlers.SysLogHandler('/var/run/log')
        else:
            handler = logging.handlers.SysLogHandler('/dev/log')
        format = f'{release.description} {release.version}:%(dbname)s:%(levelname)s:%(name)s:%(message)s'

    elif tools.config['logfile']:
        # LogFile Handler
        logf = tools.config['logfile']
        try:
            # We check we have the right location for the log files
            dirname = os.path.dirname(logf)
            if dirname and not os.path.isdir(dirname):
                os.makedirs(dirname)
            if os.name == 'posix':
                handler = WatchedFileHandler(logf)
            else:
                handler = logging.FileHandler(logf)
        except Exception:
            sys.stderr.write("ERROR: couldn't create the logfile directory. Logging to the standard output.\n")

    # Check that handler.stream has a fileno() method: when running OpenERP
    # behind Apache with mod_wsgi, handler.stream will have type mod_wsgi.Log,
    # which has no fileno() method. (mod_wsgi.Log is what is being bound to
    # sys.stderr when the logging.StreamHandler is being constructed above.)
    def is_a_tty(stream):
        return hasattr(stream, 'fileno') and os.isatty(stream.fileno())

    if os.name == 'posix' and isinstance(handler, logging.StreamHandler) and (is_a_tty(handler.stream) or os.environ.get("ODOO_PY_COLORS")):
        formatter = ColoredFormatter(format)
        perf_filter = ColoredPerfFilter()
    else:
        formatter = logging.Formatter(format)
        perf_filter = PerfFilter()
        werkzeug.serving._log_add_style = False
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)
    logging.getLogger('werkzeug').addFilter(perf_filter)

    if tools.config['log_db']:
        db_levels = {
            'debug': logging.DEBUG,
            'info': logging.INFO,
            'warning': logging.WARNING,
            'error': logging.ERROR,
            'critical': logging.CRITICAL,
        }
        postgresqlHandler = PostgreSQLHandler()
        postgresqlHandler.setLevel(int(db_levels.get(tools.config['log_db_level'], tools.config['log_db_level'])))
        logging.getLogger().addHandler(postgresqlHandler)

    # Configure loggers levels
    pseudo_config = PSEUDOCONFIG_MAPPER.get(tools.config['log_level'], [])

    logconfig = tools.config['log_handler']

    logging_configurations = DEFAULT_LOG_CONFIGURATION + pseudo_config + logconfig
    for logconfig_item in logging_configurations:
        loggername, level = logconfig_item.strip().split(':')
        level = getattr(logging, level, logging.INFO)
        logger = logging.getLogger(loggername)
        logger.setLevel(level)

    for logconfig_item in logging_configurations:
        _logger.debug('logger level set: "%s"', logconfig_item)