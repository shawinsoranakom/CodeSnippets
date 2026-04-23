def test_wrapping_characters(self):
        wrapping_chars = (
            ("()", ("(", ")")),
            ("<>", ("&lt;", "&gt;")),
            ("[]", ("[", "]")),
            ('""', ("&quot;", "&quot;")),
            ("''", ("&#x27;", "&#x27;")),
        )
        for wrapping_in, (start_out, end_out) in wrapping_chars:
            with self.subTest(wrapping_in=wrapping_in):
                start_in, end_in = wrapping_in
                self.assertEqual(
                    urlize(start_in + "https://www.example.org/" + end_in),
                    f'{start_out}<a href="https://www.example.org/" rel="nofollow">'
                    f"https://www.example.org/</a>{end_out}",
                )