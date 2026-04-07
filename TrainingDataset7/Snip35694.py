def test_str(self):
        self.assertEqual(str(RegexPattern(_("^translated/$"))), "^translated/$")