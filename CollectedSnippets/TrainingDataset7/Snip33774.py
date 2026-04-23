def test_if_is_not_variable_missing(self):
        output = self.engine.render_to_string("template", {"foo": False})
        self.assertEqual(output, "yes")