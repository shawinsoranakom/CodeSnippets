def test_help_text(self):
        self.assertEqual(
            UserAttributeSimilarityValidator().get_help_text(),
            "Your password can’t be too similar to your other personal information.",
        )