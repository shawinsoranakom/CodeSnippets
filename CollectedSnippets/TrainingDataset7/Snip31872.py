def test_setdefault(self):
        self.assertEqual(self.session.setdefault("foo", "bar"), "bar")
        self.assertEqual(self.session.setdefault("foo", "baz"), "bar")
        self.assertIs(self.session.accessed, True)
        self.assertIs(self.session.modified, True)