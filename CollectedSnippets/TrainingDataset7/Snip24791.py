def test_fromkeys_with_nonempty_value(self):
        self.assertEqual(
            QueryDict.fromkeys(["key1", "key2", "key3"], value="val"),
            QueryDict("key1=val&key2=val&key3=val"),
        )