def test_db_tablespace(self):
        field = models.Field()
        _, _, args, kwargs = field.deconstruct()
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {})
        # With a DEFAULT_DB_TABLESPACE.
        with self.settings(DEFAULT_DB_TABLESPACE="foo"):
            _, _, args, kwargs = field.deconstruct()
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {})
        # With a db_tablespace.
        field = models.Field(db_tablespace="foo")
        _, _, args, kwargs = field.deconstruct()
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"db_tablespace": "foo"})
        # With a db_tablespace equal to DEFAULT_DB_TABLESPACE.
        with self.settings(DEFAULT_DB_TABLESPACE="foo"):
            _, _, args, kwargs = field.deconstruct()
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"db_tablespace": "foo"})