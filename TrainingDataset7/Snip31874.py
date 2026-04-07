def test_update(self):
        self.session.update({"update key": 1})
        self.assertIs(self.session.accessed, True)
        self.assertIs(self.session.modified, True)
        self.assertEqual(self.session.get("update key", None), 1)