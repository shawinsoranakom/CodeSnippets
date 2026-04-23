def test_get_language_from_path_real(self):
        g = trans_real.get_language_from_path
        tests = [
            ("/pl/", "pl"),
            ("/pl", "pl"),
            ("/xyz/", None),
            ("/en/", "en"),
            ("/en-gb/", "en"),
            ("/en-latn-us/", "en-latn-us"),
            ("/en-Latn-US/", "en-Latn-US"),
            ("/de/", "de"),
            ("/de-1996/", "de-1996"),
            ("/de-at/", "de-at"),
            ("/de-AT/", "de-AT"),
            ("/de-ch/", "de"),
            ("/de-ch-1901/", "de-ch-1901"),
            ("/de-simple-page-test/", None),
            ("/i-mingo/", "i-mingo"),
            ("/kl-tunumiit/", "kl-tunumiit"),
            ("/nan-hani-tw/", "nan-hani-tw"),
            (f"/{'a' * 501}/", None),
        ]
        for path, language in tests:
            with self.subTest(path=path):
                self.assertEqual(g(path), language)