def test_nested_partials(self):
        with self.subTest(template_name="use_outer"):
            output = self.engine.render_to_string("use_outer")
            self.assertEqual(
                [line.strip() for line in output.split("\n")],
                ["It hosts a couple of partials.", "And an inner one."],
            )
        with self.subTest(template_name="use_inner"):
            output = self.engine.render_to_string("use_inner")
            self.assertEqual(output.strip(), "And an inner one.")