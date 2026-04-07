def test_valid_partialdef_names(self):
        for template_name in valid_partialdef_names:
            with self.subTest(template_name=template_name):
                output = self.engine.render_to_string(template_name)
                self.assertEqual(output, f"TEST with {template_name}!")