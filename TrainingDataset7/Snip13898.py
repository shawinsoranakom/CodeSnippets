def _pre_setup(cls):
        """
        Perform pre-test setup:
        * If the class has an 'available_apps' attribute, restrict the app
          registry to these applications, then fire the post_migrate signal --
          it must run with the correct set of applications for the test case.
        * If the class has a 'fixtures' attribute, install those fixtures.
        """
        super()._pre_setup()
        if cls.available_apps is not None:
            apps.set_available_apps(cls.available_apps)
            cls._available_apps_calls_balanced += 1
            setting_changed.send(
                sender=settings._wrapped.__class__,
                setting="INSTALLED_APPS",
                value=cls.available_apps,
                enter=True,
            )
            for db_name in cls._databases_names(include_mirrors=False):
                emit_post_migrate_signal(verbosity=0, interactive=False, db=db_name)
        try:
            cls._fixture_setup()
        except Exception:
            if cls.available_apps is not None:
                apps.unset_available_apps()
                setting_changed.send(
                    sender=settings._wrapped.__class__,
                    setting="INSTALLED_APPS",
                    value=settings.INSTALLED_APPS,
                    enter=False,
                )
            raise
        # Clear the queries_log so that it's less likely to overflow (a single
        # test probably won't execute 9K queries). If queries_log overflows,
        # then assertNumQueries() doesn't work.
        for db_name in cls._databases_names(include_mirrors=False):
            connections[db_name].queries_log.clear()