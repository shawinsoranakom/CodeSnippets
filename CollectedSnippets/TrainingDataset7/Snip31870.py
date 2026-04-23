def test_pop_no_default_keyerror_raised(self):
        with self.assertRaises(KeyError):
            self.session.pop("some key")