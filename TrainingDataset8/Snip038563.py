def test_deprecated_expired(self):
        my_value = "myValue"
        where_defined = "im defined here"

        key = "mysection.myName"

        c = ConfigOption(
            key,
            deprecated=True,
            deprecation_text="dep text",
            expiration_date="2000-01-01",
        )

        with self.assertRaises(DeprecationError):
            c.set_value(my_value, where_defined)

        self.assertTrue(c.is_expired())