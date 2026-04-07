def test_parse_literal_http_header(self):
        tests = [
            ("pt-br", "pt-br"),
            ("pt", "pt"),
            ("es,de", "es"),
            ("es-a,de", "es"),
            # There isn't a Django translation to a US variation of the Spanish
            # language, a safe assumption. When the user sets it as the
            # preferred language, the main 'es' translation should be selected
            # instead.
            ("es-us", "es"),
            # There isn't a main language (zh) translation of Django but there
            # is a translation to variation (zh-hans) the user sets zh-hans as
            # the preferred language, it should be selected without falling
            # back nor ignoring it.
            ("zh-hans,de", "zh-hans"),
            ("NL", "nl"),
            ("fy", "fy"),
            ("ia", "ia"),
            ("sr-latn", "sr-latn"),
            ("zh-hans", "zh-hans"),
            ("zh-hant", "zh-hant"),
        ]
        for header, expected in tests:
            with self.subTest(header=header):
                request = self.rf.get("/", headers={"accept-language": header})
                self.assertEqual(get_language_from_request(request), expected)