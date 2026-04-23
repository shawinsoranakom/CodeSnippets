def test_quote_lexeme(self):
        tests = (
            ("L'amour piqué par une abeille", "'L amour piqué par une abeille'"),
            ("'starting quote", "'starting quote'"),
            ("ending quote'", "'ending quote'"),
            ("double quo''te", "'double quo te'"),
            ("triple quo'''te", "'triple quo te'"),
            ("backslash\\", "'backslash'"),
            ("exclamation!", "'exclamation'"),
            ("ampers&nd", "'ampers nd'"),
        )
        for lexeme, quoted in tests:
            with self.subTest(lexeme=lexeme):
                self.assertEqual(quote_lexeme(lexeme), quoted)