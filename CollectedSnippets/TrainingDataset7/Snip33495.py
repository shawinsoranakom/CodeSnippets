def test_comment_tag05(self):
        output = self.engine.render_to_string("comment-tag05")
        self.assertEqual(output, "foo")