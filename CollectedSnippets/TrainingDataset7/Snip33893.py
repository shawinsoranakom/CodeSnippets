def test_partial_inline_and_used_once_with_before_and_after_content(self):
        output = self.engine.render_to_string("inline_partial_with_usage")
        self.assertEqual(
            output.strip(),
            "BEFORE\nHERE IS THE TEST CONTENT\nAFTER\nHERE IS THE TEST CONTENT",
        )