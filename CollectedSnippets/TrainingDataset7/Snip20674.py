def test_databases_property(self):
        # The "databases" property is maintained for backwards compatibility
        # with 3rd party packages. It should be an alias of the "settings"
        # property.
        conn = ConnectionHandler({})
        self.assertNotEqual(conn.settings, {})
        self.assertEqual(conn.settings, conn.databases)