def preload_registries(dbnames):
    """ Preload a registries, possibly run a test file."""
    # TODO: move all config checks to args dont check tools.config here
    dbnames = dbnames or []
    rc = 0

    preload_profiler = contextlib.nullcontext()

    for dbname in dbnames:
        if os.environ.get('ODOO_PROFILE_PRELOAD'):
            interval = float(os.environ.get('ODOO_PROFILE_PRELOAD_INTERVAL', '0.1'))
            collectors = [profiler.PeriodicCollector(interval=interval)]
            if os.environ.get('ODOO_PROFILE_PRELOAD_SQL'):
                collectors.append('sql')
            preload_profiler = profiler.Profiler(db=dbname, collectors=collectors)
        try:
            with preload_profiler:
                threading.current_thread().dbname = dbname
                update_module = config['init'] or config['update'] or config['reinit']

                registry = Registry.new(dbname, update_module=update_module, install_modules=config['init'], upgrade_modules=config['update'], reinit_modules=config['reinit'])

                # run post-install tests
                if config['test_enable']:
                    from odoo.tests import loader  # noqa: PLC0415
                    t0 = time.time()
                    t0_sql = sql_db.sql_counter
                    module_names = (registry.updated_modules if update_module else
                                    sorted(registry._init_modules))
                    _logger.info("Starting post tests")
                    tests_before = registry._assertion_report.testsRun
                    post_install_suite = loader.make_suite(module_names, 'post_install')
                    if post_install_suite.has_http_case():
                        with registry.cursor() as cr:
                            env = api.Environment(cr, api.SUPERUSER_ID, {})
                            env['ir.qweb']._pregenerate_assets_bundles()
                    result = loader.run_suite(post_install_suite, global_report=registry._assertion_report)
                    registry._assertion_report.update(result)
                    _logger.info("%d post-tests in %.2fs, %s queries",
                                registry._assertion_report.testsRun - tests_before,
                                time.time() - t0,
                                sql_db.sql_counter - t0_sql)

                    registry._assertion_report.log_stats()
                if registry._assertion_report and not registry._assertion_report.wasSuccessful():
                    rc += 1
        except Exception:
            _logger.critical('Failed to initialize database `%s`.', dbname, exc_info=True)
            return -1
    return rc