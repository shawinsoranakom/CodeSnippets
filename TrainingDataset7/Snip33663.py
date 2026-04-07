def test_if_tag02(self):
        output = self.engine.render_to_string("if-tag02", {"foo": False})
        self.assertEqual(output, "no")