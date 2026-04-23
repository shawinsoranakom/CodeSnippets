def test_comment_syntax09(self):
        output = self.engine.render_to_string("comment-syntax09")
        self.assertEqual(output, "foo")