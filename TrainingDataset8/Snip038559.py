def test_call(self):
        key = "mysection.myName"
        c = ConfigOption(key)

        @c
        def someRandomFunction():
            """Random docstring."""
            pass

        self.assertEqual("Random docstring.", c.description)
        self.assertEqual(someRandomFunction._get_val_func, c._get_val_func)