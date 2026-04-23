def test_non_debug(self):
        output = self.engine.render_to_string("non_debug", {})
        self.assertEqual(output, "")