def test_to_language(self):
        self.assertEqual(to_language("en_US"), "en-us")
        self.assertEqual(to_language("sr_Lat"), "sr-lat")