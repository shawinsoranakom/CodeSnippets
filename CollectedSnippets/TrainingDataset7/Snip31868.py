def test_pop_default_named_argument(self):
        self.assertEqual(
            self.session.pop("some key", default="does not exist"), "does not exist"
        )
        self.assertIs(self.session.accessed, True)
        self.assertIs(self.session.modified, False)