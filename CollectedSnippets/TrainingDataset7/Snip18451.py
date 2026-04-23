def test_repr(self):
        conn = connections[DEFAULT_DB_ALIAS]
        self.assertEqual(
            repr(conn),
            f"<DatabaseWrapper vendor={connection.vendor!r} alias='default'>",
        )