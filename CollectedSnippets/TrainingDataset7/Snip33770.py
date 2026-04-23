def test_if_is_variable_missing(self):
        output = self.engine.render_to_string("template", {"foo": 1})
        self.assertEqual(output, "no")