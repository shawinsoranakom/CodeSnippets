def test_if_tag07(self):
        output = self.engine.render_to_string("if-tag07", {"foo": True})
        self.assertEqual(output, "foo")