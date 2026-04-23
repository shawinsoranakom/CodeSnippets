def test_pop_default(self):
        self.assertEqual(
            self.session.pop("some key", "does not exist"), "does not exist"
        )
        self.assertIs(self.session.accessed, True)
        self.assertIs(self.session.modified, False)