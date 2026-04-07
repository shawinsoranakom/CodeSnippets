def setUpClass(cls):
        super().setUpClass()
        if cls._overridden_settings:
            cls.enterClassContext(override_settings(**cls._overridden_settings))
        if cls._modified_settings:
            cls.enterClassContext(modify_settings(cls._modified_settings))
        cls._add_databases_failures()
        cls.addClassCleanup(cls._remove_databases_failures)