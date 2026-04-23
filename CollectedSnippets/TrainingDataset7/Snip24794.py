def test_duplicates_in_fromkeys_iterable(self):
        self.assertEqual(QueryDict.fromkeys("xyzzy"), QueryDict("x&y&z&z&y"))