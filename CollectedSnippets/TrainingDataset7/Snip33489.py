def test_comment_syntax11(self):
        output = self.engine.render_to_string("comment-syntax11")
        self.assertEqual(output, "foo")