def test_keys(self):
        self.session["x"] = 1
        self.session.modified = False
        self.session.accessed = False
        self.assertEqual(list(self.session.keys()), ["x"])
        self.assertIs(self.session.accessed, True)
        self.assertIs(self.session.modified, False)