def test_querydict_fromkeys(self):
        self.assertEqual(
            QueryDict.fromkeys(["key1", "key2", "key3"]), QueryDict("key1&key2&key3")
        )