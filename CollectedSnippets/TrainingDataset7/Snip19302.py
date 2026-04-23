async def test_unicode(self):
        """Unicode values are ignored by the dummy cache."""
        tests = {
            "ascii": "ascii_value",
            "unicode_ascii": "Iñtërnâtiônàlizætiøn1",
            "Iñtërnâtiônàlizætiøn": "Iñtërnâtiônàlizætiøn2",
            "ascii2": {"x": 1},
        }
        for key, value in tests.items():
            with self.subTest(key=key):
                await cache.aset(key, value)
                self.assertIsNone(await cache.aget(key))