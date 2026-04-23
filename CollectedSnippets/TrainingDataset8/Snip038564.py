def test_deprecated_unexpired(self):
        my_value = "myValue"
        where_defined = "im defined here"

        key = "mysection.myName"

        c = ConfigOption(
            key,
            deprecated=True,
            deprecation_text="dep text",
            expiration_date="2100-01-01",
        )

        c.set_value(my_value, where_defined)

        self.assertFalse(c.is_expired())