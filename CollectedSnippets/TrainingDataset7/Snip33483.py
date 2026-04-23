def test_comment_syntax05(self):
        output = self.engine.render_to_string("comment-syntax05")
        self.assertEqual(output, "foo")