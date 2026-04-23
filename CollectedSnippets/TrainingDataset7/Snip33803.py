def test_include03(self):
        output = self.engine.render_to_string(
            "include03",
            {"template_name": "basic-syntax02", "headline": "Included"},
        )
        self.assertEqual(output, "Included")