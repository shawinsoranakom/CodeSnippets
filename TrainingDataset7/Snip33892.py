def test_partial_inline_and_used_once(self):
        output = self.engine.render_to_string("inline_partial_explicit_end")
        self.assertEqual(output, "HERE IS THE TEST CONTENT\nHERE IS THE TEST CONTENT")