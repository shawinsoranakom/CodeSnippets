def test_normalize_newlines(self):
        self.assertEqual(
            text.normalize_newlines("abc\ndef\rghi\r\n"), "abc\ndef\nghi\n"
        )
        self.assertEqual(text.normalize_newlines("\n\r\r\n\r"), "\n\n\n\n")
        self.assertEqual(text.normalize_newlines("abcdefghi"), "abcdefghi")
        self.assertEqual(text.normalize_newlines(""), "")
        self.assertEqual(
            text.normalize_newlines(lazystr("abc\ndef\rghi\r\n")), "abc\ndef\nghi\n"
        )