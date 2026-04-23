def test_if_tag12(self):
        output = self.engine.render_to_string("if-tag12", {"baz": True})
        self.assertEqual(output, "baz")