def test_comment_syntax10(self):
        output = self.engine.render_to_string("comment-syntax10")
        self.assertEqual(output, "foo")