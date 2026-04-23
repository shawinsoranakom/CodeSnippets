def new(
        cls,
        db_name: str,
        *,
        update_module: bool = False,
        install_modules: Collection[str] = (),
        upgrade_modules: Collection[str] = (),
        reinit_modules: Collection[str] = (),
        new_db_demo: bool | None = None,
        models_to_check: set[str] | None = None,
    ) -> Registry:
        """Create and return a new registry for the given database name.

        :param db_name: The name of the database to associate with the Registry instance.
        :param update_module: If ``True``, update modules while loading the registry. Defaults to ``False``.
        :param install_modules: Names of modules to install.

          * If a specified module is **not installed**, it and all of its direct and indirect
            dependencies will be installed.

          Defaults to an empty tuple.

        :param upgrade_modules: Names of modules to upgrade. Their direct or indirect dependent
          modules will also be upgraded. Defaults to an empty tuple.
        :param reinit_modules: Names of modules to reinitialize.

          * If a specified module is **already installed**, it and all of its installed direct and
            indirect dependents will be re-initialized. Re-initialization means the module will be
            upgraded without running upgrade scripts, but with data loaded in ``'init'`` mode.

        :param new_db_demo: Whether to install demo data for the new database. If set to ``None``, the value will be
          determined by the ``config['with_demo']``. Defaults to ``None``
        """
        t0 = time.time()
        registry: Registry = object.__new__(cls)
        registry.init(db_name)
        registry.new = registry.init = registry.registries = None  # type: ignore
        first_registry = not cls.registries

        # Initializing a registry will call general code which will in
        # turn call Registry() to obtain the registry being initialized.
        # Make it available in the registries dictionary then remove it
        # if an exception is raised.
        cls.delete(db_name)
        cls.registries[db_name] = registry  # pylint: disable=unsupported-assignment-operation
        try:
            registry.setup_signaling()
            with registry.cursor() as cr:
                # This transaction defines a critical section for multi-worker concurrency control.
                # When the transaction commits, the first worker proceeds to upgrade modules. Other workers
                # encounter a serialization error and retry, finding no upgrade marker in the database.
                # This significantly reduces the likelihood of concurrent module upgrades across workers.
                # NOTE: This block is intentionally outside the try-except below to prevent workers that fail
                # due to serialization errors from calling `reset_modules_state` while the first worker is
                # actively upgrading modules.
                from odoo.modules import db  # noqa: PLC0415
                if db.is_initialized(cr):
                    cr.execute("DELETE FROM ir_config_parameter WHERE key='base.partially_updated_database'")
                    if cr.rowcount:
                        update_module = True
            # This should be a method on Registry
            from odoo.modules.loading import load_modules, reset_modules_state  # noqa: PLC0415
            exit_stack = ExitStack()
            try:
                if upgrade_modules or install_modules or reinit_modules:
                    update_module = True
                if new_db_demo is None:
                    new_db_demo = config['with_demo']
                if first_registry and not update_module:
                    exit_stack.enter_context(gc.disabling_gc())
                load_modules(
                    registry,
                    update_module=update_module,
                    upgrade_modules=upgrade_modules,
                    install_modules=install_modules,
                    reinit_modules=reinit_modules,
                    new_db_demo=new_db_demo,
                    models_to_check=models_to_check,
                )
            except Exception:
                reset_modules_state(db_name)
                raise
            finally:
                exit_stack.close()
        except Exception:
            _logger.error('Failed to load registry')
            del cls.registries[db_name]     # pylint: disable=unsupported-delete-operation
            raise

        del registry._reinit_modules

        # load_modules() above can replace the registry by calling
        # indirectly new() again (when modules have to be uninstalled).
        # Yeah, crazy.
        registry = cls.registries[db_name]  # pylint: disable=unsubscriptable-object

        registry._init = False
        registry.ready = True
        registry.registry_invalidated = bool(update_module)
        registry.signal_changes()

        _logger.info("Registry loaded in %.3fs", time.time() - t0)
        return registry