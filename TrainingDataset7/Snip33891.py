def test_partial_inline_only_with_before_and_after_content(self):
        output = self.engine.render_to_string("inline_partial_with_context")
        self.assertEqual(output.strip(), "BEFORE\nHERE IS THE TEST CONTENT\nAFTER")