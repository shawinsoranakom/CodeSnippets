def test_items(self):
        self.session["x"] = 1
        self.session.modified = False
        self.session.accessed = False
        self.assertEqual(list(self.session.items()), [("x", 1)])
        self.assertIs(self.session.accessed, True)
        self.assertIs(self.session.modified, False)