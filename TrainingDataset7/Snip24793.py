def test_fromkeys_mutable_override(self):
        q = QueryDict.fromkeys(["key1", "key2", "key3"], mutable=True)
        q["key4"] = "yep"
        self.assertEqual(q, QueryDict("key1&key2&key3&key4=yep"))