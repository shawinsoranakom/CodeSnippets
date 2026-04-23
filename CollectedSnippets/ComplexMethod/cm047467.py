def load_modules(
    registry: Registry,
    *,
    update_module: bool = False,
    upgrade_modules: Collection[str] = (),
    install_modules: Collection[str] = (),
    reinit_modules: Collection[str] = (),
    new_db_demo: bool = False,
    models_to_check: OrderedSet[str] | None = None,
) -> None:
    """ Load the modules for a registry object that has just been created.  This
        function is part of Registry.new() and should not be used anywhere else.

        :param registry: The new inited registry object used to load modules.
        :param update_module: Whether to update (install, upgrade, or uninstall) modules. Defaults to ``False``
        :param upgrade_modules: A collection of module names to upgrade.
        :param install_modules: A collection of module names to install.
        :param reinit_modules: A collection of module names to reinitialize.
        :param new_db_demo: Whether to install demo data for new database. Defaults to ``False``
    """
    if models_to_check is None:
        models_to_check = OrderedSet()

    initialize_sys_path()

    with registry.cursor() as cr:
        # prevent endless wait for locks on schema changes (during online
        # installs) if a concurrent transaction has accessed the table;
        # connection settings are automatically reset when the connection is
        # borrowed from the pool
        cr.execute("SET SESSION lock_timeout = '15s'")
        if not modules_db.is_initialized(cr):
            if not update_module:
                _logger.error("Database %s not initialized, you can force it with `-i base`", cr.dbname)
                return
            _logger.info("Initializing database %s", cr.dbname)
            modules_db.initialize(cr)
        elif 'base' in reinit_modules:
            registry._reinit_modules.add('base')

        if 'base' in upgrade_modules:
            cr.execute("update ir_module_module set state=%s where name=%s and state=%s", ('to upgrade', 'base', 'installed'))

        # STEP 1: LOAD BASE (must be done before module dependencies can be computed for later steps)
        graph = ModuleGraph(cr, mode='update' if update_module else 'load')
        graph.extend(['base'])
        if not graph:
            _logger.critical('module base cannot be loaded! (hint: verify addons-path)')
            raise ImportError('Module `base` cannot be loaded! (hint: verify addons-path)')
        if update_module and upgrade_modules:
            for pyfile in tools.config['pre_upgrade_scripts']:
                odoo.modules.migration.exec_script(cr, graph['base'].installed_version, pyfile, 'base', 'pre')

        if update_module and tools.sql.table_exists(cr, 'ir_model_fields'):
            # determine the fields which are currently translated in the database
            cr.execute("SELECT model || '.' || name, translate FROM ir_model_fields WHERE translate IS NOT NULL")
            registry._database_translated_fields = dict(cr.fetchall())

            # determine the fields which are currently company dependent in the database
            if odoo.tools.sql.column_exists(cr, 'ir_model_fields', 'company_dependent'):
                cr.execute("SELECT model || '.' || name FROM ir_model_fields WHERE company_dependent IS TRUE")
                registry._database_company_dependent_fields = {row[0] for row in cr.fetchall()}

        report = registry._assertion_report
        env = api.Environment(cr, api.SUPERUSER_ID, {})
        load_module_graph(
            env,
            graph,
            update_module=update_module,
            report=report,
            models_to_check=models_to_check,
            install_demo=new_db_demo,
        )

        load_lang = tools.config._cli_options.pop('load_language', None)
        if load_lang or update_module:
            # some base models are used below, so make sure they are set up
            registry._setup_models__(cr, [])  # incremental setup

        if load_lang:
            for lang in load_lang.split(','):
                tools.translate.load_language(cr, lang)

        # STEP 2: Mark other modules to be loaded/updated
        if update_module:
            Module = env['ir.module.module']
            _logger.info('updating modules list')
            Module.update_list()

            _check_module_names(cr, itertools.chain(install_modules, upgrade_modules))

            if install_modules:
                modules = Module.search([('state', '=', 'uninstalled'), ('name', 'in', tuple(install_modules))])
                if modules:
                    modules.button_install()

            if upgrade_modules:
                modules = Module.search([('state', 'in', ('installed', 'to upgrade')), ('name', 'in', tuple(upgrade_modules))])
                if modules:
                    modules.button_upgrade()

            if reinit_modules:
                modules = Module.search([('state', 'in', ('installed', 'to upgrade')), ('name', 'in', tuple(reinit_modules))])
                reinit_modules = modules.downstream_dependencies(exclude_states=('uninstalled', 'uninstallable', 'to remove', 'to install')) + modules
                registry._reinit_modules.update(m for m in reinit_modules.mapped('name') if m not in graph._imported_modules)

            env.flush_all()
            cr.execute("update ir_module_module set state=%s where name=%s", ('installed', 'base'))
            Module.invalidate_model(['state'])

        # STEP 3: Load marked modules (skipping base which was done in STEP 1)
        # loop this step in case extra modules' states are changed to 'to install'/'to update' during loading
        while True:
            if update_module:
                states = ('installed', 'to upgrade', 'to remove', 'to install')
            else:
                states = ('installed', 'to upgrade', 'to remove')
            env.cr.execute("SELECT name from ir_module_module WHERE state IN %s", [states])
            module_list = [name for (name,) in env.cr.fetchall() if name not in graph]
            if not module_list:
                break
            graph.extend(module_list)
            _logger.debug('Updating graph with %d more modules', len(module_list))
            updated_modules_count = len(registry.updated_modules)
            load_module_graph(
                env, graph, update_module=update_module,
                report=report, models_to_check=models_to_check)
            if len(registry.updated_modules) == updated_modules_count:
                break

        if update_module:
            # set up the registry without the patch for translated fields
            database_translated_fields = registry._database_translated_fields
            registry._database_translated_fields = {}
            registry._setup_models__(cr, [])  # incremental setup
            # determine which translated fields should no longer be translated,
            # and make their model fix the database schema
            models_to_untranslate = set()
            for full_name in database_translated_fields:
                model_name, field_name = full_name.rsplit('.', 1)
                if model_name in registry:
                    field = registry[model_name]._fields.get(field_name)
                    if field and not field.translate:
                        _logger.debug("Making field %s non-translated", field)
                        models_to_untranslate.add(model_name)
            registry.init_models(cr, list(models_to_untranslate), {'models_to_check': True})

        registry.loaded = True
        registry._setup_models__(cr)

        # check that all installed modules have been loaded by the registry
        Module = env['ir.module.module']
        modules = Module.search_fetch(Module._get_modules_to_load_domain(), ['name'], order='name')
        missing = [name for name in modules.mapped('name') if name not in graph]
        if missing:
            _logger.error("Some modules are not loaded, some dependencies or manifest may be missing: %s", missing)

        # STEP 3.5: execute migration end-scripts
        if update_module:
            migrations = MigrationManager(cr, graph)
            for package in graph:
                migrations.migrate_module(package, 'end')

        # check that new module dependencies have been properly installed after a migration/upgrade
        cr.execute("SELECT name from ir_module_module WHERE state IN ('to install', 'to upgrade')")
        module_list = [name for (name,) in cr.fetchall()]
        if module_list:
            _logger.error("Some modules have inconsistent states, some dependencies may be missing: %s", sorted(module_list))

        # STEP 3.6: apply remaining constraints in case of an upgrade
        registry.finalize_constraints(cr)

        # STEP 4: Finish and cleanup installations
        if registry.updated_modules:

            cr.execute("SELECT model from ir_model")
            for (model,) in cr.fetchall():
                if model in registry:
                    env[model]._check_removed_columns(log=True)
                elif _logger.isEnabledFor(logging.INFO):    # more an info that a warning...
                    _logger.runbot("Model %s is declared but cannot be loaded! (Perhaps a module was partially removed or renamed)", model)

            # Cleanup orphan records
            env['ir.model.data']._process_end(registry.updated_modules)
            # Cleanup cron
            vacuum_cron = env.ref('base.autovacuum_job', raise_if_not_found=False)
            if vacuum_cron:
                # trigger after a small delay to give time for assets to regenerate
                vacuum_cron._trigger(at=datetime.datetime.now() + datetime.timedelta(minutes=1))

            env.flush_all()

        # STEP 5: Uninstall modules to remove
        if update_module:
            # Remove records referenced from ir_model_data for modules to be
            # removed (and removed the references from ir_model_data).
            cr.execute("SELECT name, id FROM ir_module_module WHERE state=%s", ('to remove',))
            modules_to_remove = dict(cr.fetchall())
            if modules_to_remove:
                pkgs = reversed([p for p in graph if p.name in modules_to_remove])
                for pkg in pkgs:
                    uninstall_hook = pkg.manifest.get('uninstall_hook')
                    if uninstall_hook:
                        py_module = sys.modules['odoo.addons.%s' % (pkg.name,)]
                        getattr(py_module, uninstall_hook)(env)
                        env.flush_all()

                Module = env['ir.module.module']
                Module.browse(modules_to_remove.values()).module_uninstall()
                # Recursive reload, should only happen once, because there should be no
                # modules to remove next time
                cr.commit()
                _logger.info('Reloading registry once more after uninstalling modules')
                registry = Registry.new(
                    cr.dbname, update_module=update_module, models_to_check=models_to_check,
                )
                return

        # STEP 5.5: Verify extended fields on every model
        # This will fix the schema of all models in a situation such as:
        #   - module A is loaded and defines model M;
        #   - module B is installed/upgraded and extends model M;
        #   - module C is loaded and extends model M;
        #   - module B and C depend on A but not on each other;
        # The changes introduced by module C are not taken into account by the upgrade of B.
        if update_module:
            # We need to fix custom fields for which we have dropped the not-null constraint.
            cr.execute("""SELECT DISTINCT model FROM ir_model_fields WHERE state = 'manual'""")
            models_to_check.update(model_name for model_name, in cr.fetchall() if model_name in registry)
        if models_to_check:
            # Doesn't check models that didn't exist anymore, it might happen during uninstallation
            models_to_check = [model for model in models_to_check if model in registry]
            registry.init_models(cr, models_to_check, {'models_to_check': True, 'update_custom_fields': True})

        # STEP 6: verify custom views on every model
        if update_module:
            View = env['ir.ui.view']
            for model in registry:
                try:
                    View._validate_custom_views(model)
                except Exception as e:
                    _logger.warning('invalid custom view(s) for model %s: %s', model, e)

        if not registry._assertion_report or registry._assertion_report.wasSuccessful():
            _logger.info('Modules loaded.')
        else:
            _logger.error('At least one test failed when loading the modules.')

        # STEP 9: call _register_hook on every model
        # This is done *exactly once* when the registry is being loaded. See the
        # management of those hooks in `Registry._setup_models__`: all the calls to
        # _setup_models__() done here do not mess up with hooks, as registry.ready
        # is False.
        for model in env.values():
            model._register_hook()
        env.flush_all()

        # STEP 10: check that we can trust nullable columns
        registry.check_null_constraints(cr)

        if update_module:
            cr.execute(
                """
                INSERT INTO ir_config_parameter(key, value)
                SELECT 'base.partially_updated_database', '1'
                WHERE EXISTS(SELECT FROM ir_module_module WHERE state IN ('to upgrade', 'to install', 'to remove'))
                ON CONFLICT DO NOTHING
                """
            )