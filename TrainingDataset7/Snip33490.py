def test_comment_syntax12(self):
        output = self.engine.render_to_string("comment-syntax12")
        self.assertEqual(output, "foo")