def test_comment_syntax01(self):
        output = self.engine.render_to_string("comment-syntax01")
        self.assertEqual(output, "hello")