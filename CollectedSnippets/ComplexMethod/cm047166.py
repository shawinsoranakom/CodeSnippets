def report_configuration():
    """ Log the server version and some configuration values.

    This function assumes the configuration has been initialized.
    """
    import odoo.addons  # noqa: PLC0415
    import odoo.release  # noqa: PLC0415
    _logger.info("Odoo version %s", odoo.release.version)
    if os.path.isfile(config['config']):
        _logger.info("Using configuration file at %s", config['config'])
    _logger.info('addons paths: %s', odoo.addons.__path__)
    if config.get('upgrade_path'):
        _logger.info('upgrade path: %s', config['upgrade_path'])
    if config.get('pre_upgrade_scripts'):
        _logger.info('extra upgrade scripts: %s', config['pre_upgrade_scripts'])
    host = config['db_host'] or os.environ.get('PGHOST', 'default')
    port = config['db_port'] or os.environ.get('PGPORT', 'default')
    user = config['db_user'] or os.environ.get('PGUSER', 'default')
    _logger.info('database: %s@%s:%s', user, host, port)
    replica_host = config['db_replica_host']
    replica_port = config['db_replica_port']
    if replica_host or replica_port or 'replica' in config['dev_mode']:
        _logger.info('replica database: %s@%s:%s', user, replica_host or 'default', replica_port or 'default')
    if sys.version_info[:2] > odoo.release.MAX_PY_VERSION:
        _logger.warning("Python %s is not officially supported, please use Python %s instead",
            '.'.join(map(str, sys.version_info[:2])),
            '.'.join(map(str, odoo.release.MAX_PY_VERSION))
        )