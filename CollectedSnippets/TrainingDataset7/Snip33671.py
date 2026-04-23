def test_if_tag10(self):
        output = self.engine.render_to_string("if-tag10", {"foo": True})
        self.assertEqual(output, "foo")