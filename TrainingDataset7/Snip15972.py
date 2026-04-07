def test_quote(self):
        self.assertEqual(quote("something\nor\nother"), "something_0Aor_0Aother")