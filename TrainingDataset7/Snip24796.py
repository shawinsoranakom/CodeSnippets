def test_fromkeys_empty_iterable(self):
        self.assertEqual(QueryDict.fromkeys([]), QueryDict(""))