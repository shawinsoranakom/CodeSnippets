def test_nonexistent_feature(self):
        self.assertFalse(hasattr(connection.features, "nonexistent"))