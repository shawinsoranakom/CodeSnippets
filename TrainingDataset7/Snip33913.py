def assertRenderEqual(self, template_name, context, expected):
        output = self.engine.render_to_string(template_name, context)
        self.assertEqual(output, expected)