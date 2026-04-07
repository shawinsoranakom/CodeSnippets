def test_basic_usage(self):
        for template_name in (
            "basic",
            "basic_inline",
            "inline_inline",
            "with_newlines",
        ):
            with self.subTest(template_name=template_name):
                output = self.engine.render_to_string(template_name)
                self.assertEqual(output.strip(), "HERE IS THE TEST CONTENT")