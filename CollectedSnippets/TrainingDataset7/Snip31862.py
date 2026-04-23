def test_store(self):
        self.session["cat"] = "dog"
        self.assertIs(self.session.modified, True)
        self.assertEqual(self.session.pop("cat"), "dog")