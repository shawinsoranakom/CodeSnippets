def test_if_is_no_match(self):
        output = self.engine.render_to_string("template", {"foo": 1})
        self.assertEqual(output, "no")