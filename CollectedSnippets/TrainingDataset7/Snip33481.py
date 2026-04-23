def test_comment_syntax03(self):
        output = self.engine.render_to_string("comment-syntax03")
        self.assertEqual(output, "foo")