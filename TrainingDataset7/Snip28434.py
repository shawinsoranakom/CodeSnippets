def test_big_integer_field(self):
        bif = BigIntForm({"biggie": "-9223372036854775808"})
        self.assertTrue(bif.is_valid())
        bif = BigIntForm({"biggie": "-9223372036854775809"})
        self.assertFalse(bif.is_valid())
        self.assertEqual(
            bif.errors,
            {
                "biggie": [
                    "Ensure this value is greater than or equal to "
                    "-9223372036854775808."
                ]
            },
        )
        bif = BigIntForm({"biggie": "9223372036854775807"})
        self.assertTrue(bif.is_valid())
        bif = BigIntForm({"biggie": "9223372036854775808"})
        self.assertFalse(bif.is_valid())
        self.assertEqual(
            bif.errors,
            {
                "biggie": [
                    "Ensure this value is less than or equal to 9223372036854775807."
                ]
            },
        )