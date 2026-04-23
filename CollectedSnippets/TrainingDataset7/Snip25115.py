def test_get_supported_language_variant_real(self):
        g = trans_real.get_supported_language_variant
        self.assertEqual(g("en"), "en")
        self.assertEqual(g("en-gb"), "en")
        self.assertEqual(g("de"), "de")
        self.assertEqual(g("de-at"), "de-at")
        self.assertEqual(g("de-ch"), "de")
        self.assertEqual(g("pt-br"), "pt-br")
        self.assertEqual(g("pt-BR"), "pt-BR")
        self.assertEqual(g("pt"), "pt-br")
        self.assertEqual(g("pt-pt"), "pt-br")
        self.assertEqual(g("ar-dz"), "ar-dz")
        self.assertEqual(g("ar-DZ"), "ar-DZ")
        with self.assertRaises(LookupError):
            g("pt", strict=True)
        with self.assertRaises(LookupError):
            g("pt-pt", strict=True)
        with self.assertRaises(LookupError):
            g("xyz")
        with self.assertRaises(LookupError):
            g("xy-zz")
        with self.assertRaises(LookupError):
            g("x" * LANGUAGE_CODE_MAX_LENGTH)
        with self.assertRaises(LookupError):
            g("x" * (LANGUAGE_CODE_MAX_LENGTH + 1))
        # 167 * 3 = 501 which is LANGUAGE_CODE_MAX_LENGTH + 1.
        self.assertEqual(g("en-" * 167), "en")
        with self.assertRaises(LookupError):
            g("en-" * 167, strict=True)
        self.assertEqual(g("en-" * 30000), "en")