def test_if_tag04(self):
        output = self.engine.render_to_string("if-tag04", {"foo": True})
        self.assertEqual(output, "foo")