def test_phone2numeric(self):
        self.assertEqual(phone2numeric_filter("0800 flowers"), "0800 3569377")