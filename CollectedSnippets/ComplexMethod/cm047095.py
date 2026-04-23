def connection_info_for(db_or_uri: str, readonly=False) -> tuple[str, dict]:
    """ parse the given `db_or_uri` and return a 2-tuple (dbname, connection_params)

    Connection params are either a dictionary with a single key ``dsn``
    containing a connection URI, or a dictionary containing connection
    parameter keywords which psycopg2 can build a key/value connection string
    (dsn) from

    :param str db_or_uri: database name or postgres dsn
    :param bool readonly: used to load
        the default configuration from ``db_`` or ``db_replica_``.
    :rtype: (str, dict)
    """
    app_name = config['db_app_name']
    if 'ODOO_PGAPPNAME' in os.environ:
        warnings.warn("Since 19.0, use PGAPPNAME instead of ODOO_PGAPPNAME", DeprecationWarning)
        app_name = os.environ['ODOO_PGAPPNAME']
    # Using manual string interpolation for security reason and trimming at default NAMEDATALEN=63
    app_name = app_name.replace('{pid}', str(os.getpid()))[:63]
    if db_or_uri.startswith(('postgresql://', 'postgres://')):
        # extract db from uri
        us = urls.url_parse(db_or_uri)  # type: ignore
        if len(us.path) > 1:
            db_name = us.path[1:]
        elif us.username:
            db_name = us.username
        else:
            db_name = us.hostname
        return db_name, {'dsn': db_or_uri, 'application_name': app_name}

    connection_info = {'database': db_or_uri, 'application_name': app_name}
    for p in ('host', 'port', 'user', 'password', 'sslmode'):
        cfg = tools.config['db_' + p]
        if readonly:
            cfg = tools.config.get('db_replica_' + p) or cfg
        if cfg:
            connection_info[p] = cfg

    return db_or_uri, connection_info