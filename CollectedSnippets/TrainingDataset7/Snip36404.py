def test_urlize_unchanged_inputs(self):
        tests = (
            ("a" + "@a" * 50000) + "a",  # simple_email_re catastrophic test
            # Unicode domain catastrophic tests.
            "a@" + "한.글." * 1_000_000 + "a",
            "http://" + "한.글." * 1_000_000 + "com",
            "www." + "한.글." * 1_000_000 + "com",
            ("a" + "." * 1000000) + "a",  # trailing_punctuation catastrophic test
            "foo@",
            "@foo.com",
            "foo@.example.com",
            "foo@localhost",
            "foo@localhost.",
            "test@example?;+!.com",
            "email me@example.com,then I'll respond",
            "[a link](https://www.djangoproject.com/)",
            # trim_punctuation catastrophic tests
            "(" * 100_000 + ":" + ")" * 100_000,
            "(" * 100_000 + "&:" + ")" * 100_000,
            "([" * 100_000 + ":" + "])" * 100_000,
            "[(" * 100_000 + ":" + ")]" * 100_000,
            "([[" * 100_000 + ":" + "]])" * 100_000,
            "&:" + ";" * 100_000,
            "&.;" * 100_000,
            ".;" * 100_000,
            "&" + ";:" * 100_000,
        )
        for value in tests:
            with self.subTest(value=value):
                self.assertEqual(urlize(value), value)