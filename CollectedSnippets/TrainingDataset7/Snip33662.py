def test_if_tag01(self):
        output = self.engine.render_to_string("if-tag01", {"foo": True})
        self.assertEqual(output, "yes")