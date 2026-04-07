def test_date02_l10n(self):
        """Without arg, the active language's DATE_FORMAT is used."""
        with translation.override("fr"):
            output = self.engine.render_to_string(
                "date02_l10n", {"d": datetime(2008, 1, 1)}
            )
        self.assertEqual(output, "1 janvier 2008")