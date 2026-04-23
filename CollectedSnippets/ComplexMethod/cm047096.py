def db_connect(to: str, allow_uri=False, readonly=False) -> Connection:
    global _Pool, _Pool_readonly  # noqa: PLW0603 (global-statement)

    maxconn = (tools.config['db_maxconn_gevent'] if hasattr(odoo, 'evented') and odoo.evented else 0) or tools.config['db_maxconn']
    _Pool_readonly if readonly else _Pool
    if readonly:
        if _Pool_readonly is None:
            _Pool_readonly = ConnectionPool(int(maxconn), readonly=True)
        pool = _Pool_readonly
    else:
        if _Pool is None:
            _Pool = ConnectionPool(int(maxconn), readonly=False)
        pool = _Pool

    db, info = connection_info_for(to, readonly)
    if not allow_uri and db != to:
        raise ValueError('URI connections not allowed')
    return Connection(pool, db, info)