def test_subsequent_code_fallback_language(self):
        """
        Subsequent language codes should be used when the language code is not
        supported.
        """
        tests = [
            ("zh-Hans-CN", "zh-hans"),
            ("zh-hans-mo", "zh-hans"),
            ("zh-hans-HK", "zh-hans"),
            ("zh-Hant-HK", "zh-hant"),
            ("zh-hant-tw", "zh-hant"),
            ("zh-hant-SG", "zh-hant"),
        ]
        for value, expected in tests:
            with self.subTest(value=value):
                request = self.rf.get("/", headers={"accept-language": f"{value},en"})
                self.assertEqual(get_language_from_request(request), expected)