def test_i18n28(self):
        """simple translation of multiple variables"""
        output = self.engine.render_to_string("i18n28", {"anton": "α", "berta": "β"})
        self.assertEqual(output, "α + β")