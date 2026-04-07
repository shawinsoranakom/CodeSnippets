def test_connect_isolation_level(self):
        self.assertEqual(
            self.get_isolation_level(connection), self.configured_isolation_level
        )