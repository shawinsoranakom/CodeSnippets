def test_support_for_deprecated_chinese_language_codes(self):
        """
        Some browsers (Firefox, IE, etc.) use deprecated language codes. As
        these language codes will be removed in Django 1.9, these will be
        incorrectly matched. For example zh-tw (traditional) will be
        interpreted as zh-hans (simplified), which is wrong. So we should also
        accept these deprecated language codes.

        refs #18419 -- this is explicitly for browser compatibility
        """
        g = get_language_from_request
        request = self.rf.get("/", headers={"accept-language": "zh-cn,en"})
        self.assertEqual(g(request), "zh-hans")

        request = self.rf.get("/", headers={"accept-language": "zh-tw,en"})
        self.assertEqual(g(request), "zh-hant")