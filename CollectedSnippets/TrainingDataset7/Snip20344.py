def test_invalid_collation(self):
        tests = [
            None,
            "",
            'et-x-icu" OR ',
            '"schema"."collation"',
        ]
        msg = "Invalid collation name: %r."
        for value in tests:
            with self.subTest(value), self.assertRaisesMessage(ValueError, msg % value):
                Collate(F("alias"), value)