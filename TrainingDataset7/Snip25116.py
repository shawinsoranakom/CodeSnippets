def test_get_supported_language_variant_null(self):
        g = trans_null.get_supported_language_variant
        self.assertEqual(g(settings.LANGUAGE_CODE), settings.LANGUAGE_CODE)
        with self.assertRaises(LookupError):
            g("pt")
        with self.assertRaises(LookupError):
            g("de")
        with self.assertRaises(LookupError):
            g("de-at")
        with self.assertRaises(LookupError):
            g("de", strict=True)
        with self.assertRaises(LookupError):
            g("de-at", strict=True)
        with self.assertRaises(LookupError):
            g("xyz")