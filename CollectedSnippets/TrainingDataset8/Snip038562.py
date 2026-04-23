def test_set_value(self):
        my_value = "myValue"
        where_defined = "im defined here"

        key = "mysection.myName"
        c = ConfigOption(key)
        c.set_value(my_value, where_defined)

        self.assertEqual(my_value, c.value)
        self.assertEqual(where_defined, c.where_defined)