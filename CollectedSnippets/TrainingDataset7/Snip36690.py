def test_wrap(self):
        digits = "1234 67 9"
        self.assertEqual(text.wrap(digits, 100), "1234 67 9")
        self.assertEqual(text.wrap(digits, 9), "1234 67 9")
        self.assertEqual(text.wrap(digits, 8), "1234 67\n9")

        self.assertEqual(text.wrap("short\na long line", 7), "short\na long\nline")
        self.assertEqual(
            text.wrap("do-not-break-long-words please? ok", 8),
            "do-not-break-long-words\nplease?\nok",
        )

        long_word = "l%sng" % ("o" * 20)
        self.assertEqual(text.wrap(long_word, 20), long_word)
        self.assertEqual(
            text.wrap("a %s word" % long_word, 10), "a\n%s\nword" % long_word
        )
        self.assertEqual(text.wrap(lazystr(digits), 100), "1234 67 9")