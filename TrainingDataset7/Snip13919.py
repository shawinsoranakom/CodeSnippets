def _fixture_setup(cls):
        if not cls._databases_support_transactions():
            # If the backend does not support transactions, we should reload
            # class data before each test
            cls.setUpTestData()
            return super()._fixture_setup()

        if cls.reset_sequences:
            raise TypeError("reset_sequences cannot be used on TestCase instances")
        cls.atomics = cls._enter_atomics()
        if not cls._databases_support_savepoints():
            if cls.fixtures:
                for db_name in cls._databases_names(include_mirrors=False):
                    call_command(
                        "loaddata",
                        *cls.fixtures,
                        **{"verbosity": 0, "database": db_name},
                    )
            cls.setUpTestData()