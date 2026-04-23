def test_comment_syntax08(self):
        output = self.engine.render_to_string("comment-syntax08")
        self.assertEqual(output, "foobar")