def test_help_text_overrides(self):
        form = FieldOverridesByFormMetaForm()
        self.assertEqual(
            form["slug"].help_text,
            "Watch out! Letters, numbers, underscores and hyphens only.",
        )