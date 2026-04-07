def test_if_is_not_no_match(self):
        output = self.engine.render_to_string("template", {"foo": None})
        self.assertEqual(output, "no")