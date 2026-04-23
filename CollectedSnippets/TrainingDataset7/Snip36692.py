def test_phone2numeric(self):
        numeric = text.phone2numeric("0800 flowers")
        self.assertEqual(numeric, "0800 3569377")
        lazy_numeric = lazystr(text.phone2numeric("0800 flowers"))
        self.assertEqual(lazy_numeric, "0800 3569377")