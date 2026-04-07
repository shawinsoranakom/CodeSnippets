def setUpClass(cls):
        super().setUpClass()
        cls._initial_table_names = frozenset(connection.introspection.table_names())