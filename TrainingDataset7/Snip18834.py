def test_cached_db_features(self):
        self.assertIn(connection.features.supports_transactions, (True, False))
        self.assertIn(connection.features.can_introspect_foreign_keys, (True, False))