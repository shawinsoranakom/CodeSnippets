def test_comment_syntax02(self):
        output = self.engine.render_to_string("comment-syntax02")
        self.assertEqual(output, "hello")