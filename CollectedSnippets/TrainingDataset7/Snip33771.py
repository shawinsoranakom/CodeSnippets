def test_if_is_both_variables_missing(self):
        output = self.engine.render_to_string("template", {})
        self.assertEqual(output, "yes")