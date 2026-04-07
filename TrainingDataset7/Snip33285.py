def test_i18n17(self):
        """
        Escaping inside blocktranslate and translate works as if it was
        directly in the template.
        """
        output = self.engine.render_to_string("i18n17", {"anton": "α & β"})
        self.assertEqual(output, "α &amp; β")