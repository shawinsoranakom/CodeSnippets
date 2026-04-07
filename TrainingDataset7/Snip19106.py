def test_unicode(self):
        # Unicode values can be cached
        stuff = {
            "ascii": "ascii_value",
            "unicode_ascii": "Iñtërnâtiônàlizætiøn1",
            "Iñtërnâtiônàlizætiøn": "Iñtërnâtiônàlizætiøn2",
            "ascii2": {"x": 1},
        }
        # Test `set`
        for key, value in stuff.items():
            with self.subTest(key=key):
                cache.set(key, value)
                self.assertEqual(cache.get(key), value)

        # Test `add`
        for key, value in stuff.items():
            with self.subTest(key=key):
                self.assertIs(cache.delete(key), True)
                self.assertIs(cache.add(key, value), True)
                self.assertEqual(cache.get(key), value)

        # Test `set_many`
        for key, value in stuff.items():
            self.assertIs(cache.delete(key), True)
        cache.set_many(stuff)
        for key, value in stuff.items():
            with self.subTest(key=key):
                self.assertEqual(cache.get(key), value)