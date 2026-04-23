def test_value(self):
        my_value = "myValue"

        key = "mysection.myName"
        c = ConfigOption(key)

        @c
        def someRandomFunction():
            """Random docstring."""
            return my_value

        self.assertEqual(my_value, c.value)