def test_comment_syntax04(self):
        output = self.engine.render_to_string("comment-syntax04")
        self.assertEqual(output, "foo")