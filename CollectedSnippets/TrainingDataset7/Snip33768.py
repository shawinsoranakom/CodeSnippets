def test_if_is_match(self):
        output = self.engine.render_to_string("template", {"foo": True})
        self.assertEqual(output, "yes")