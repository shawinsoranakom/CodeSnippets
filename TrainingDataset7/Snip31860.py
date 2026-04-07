def test_get_empty(self):
        self.assertIsNone(self.session.get("cat"))