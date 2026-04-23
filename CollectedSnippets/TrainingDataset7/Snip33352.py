def test_i18n23(self):
        """Using filters with the {% translate %} tag (#5972)."""
        with translation.override("de"):
            output = self.engine.render_to_string("i18n23")
        self.assertEqual(output, "nicht gefunden")