def test_comment_syntax07(self):
        output = self.engine.render_to_string("comment-syntax07")
        self.assertEqual(output, "foo")