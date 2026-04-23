def test_legacyi18n28(self):
        output = self.engine.render_to_string(
            "legacyi18n28", {"anton": "α", "berta": "β"}
        )
        self.assertEqual(output, "α + β")