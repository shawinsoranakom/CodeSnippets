def test_equal(self):
        self.assertEqual(
            OrderBy(F("field"), nulls_last=True),
            OrderBy(F("field"), nulls_last=True),
        )
        self.assertNotEqual(
            OrderBy(F("field"), nulls_last=True),
            OrderBy(F("field")),
        )