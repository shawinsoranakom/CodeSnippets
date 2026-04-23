def test_render_built_in_type_method(self):
        """
        Templates should not crash when rendering methods for built-in types
        without required arguments.
        """
        template = self._engine().from_string("{{ description.count }}")
        self.assertEqual(template.render(Context({"description": "test"})), "")