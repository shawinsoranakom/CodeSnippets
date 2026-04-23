def test_quotes(self):
        self.assertEqual(
            addslashes("\"double quotes\" and 'single quotes'"),
            "\\\"double quotes\\\" and \\'single quotes\\'",
        )