def setUpClass(cls):
        super().setUpClass()
        configured_isolation_level = (
            connection.isolation_level or cls.isolation_values[cls.repeatable_read]
        )
        cls.configured_isolation_level = configured_isolation_level.upper()
        cls.other_isolation_level = (
            cls.read_committed
            if configured_isolation_level != cls.isolation_values[cls.read_committed]
            else cls.repeatable_read
        )