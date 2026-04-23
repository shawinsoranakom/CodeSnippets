def test_unicode(self):
        "Unicode values are ignored by the dummy cache"
        stuff = {
            "ascii": "ascii_value",
            "unicode_ascii": "Iñtërnâtiônàlizætiøn1",
            "Iñtërnâtiônàlizætiøn": "Iñtërnâtiônàlizætiøn2",
            "ascii2": {"x": 1},
        }
        for key, value in stuff.items():
            with self.subTest(key=key):
                cache.set(key, value)
                self.assertIsNone(cache.get(key))