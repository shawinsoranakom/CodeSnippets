def test_hash(self):
        self.assertEqual(
            hash(OrderBy(F("field"), nulls_last=True)),
            hash(OrderBy(F("field"), nulls_last=True)),
        )
        self.assertNotEqual(
            hash(OrderBy(F("field"), nulls_last=True)),
            hash(OrderBy(F("field"))),
        )