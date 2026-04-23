def test_autoescape_filters02(self):
        output = self.engine.render_to_string(
            "autoescape-filters02", {"var": ("Tom", "Dick", "Harry")}
        )
        self.assertEqual(output, "Tom & Dick & Harry")