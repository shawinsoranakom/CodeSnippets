def test_comment_tag03(self):
        output = self.engine.render_to_string("comment-tag03")
        self.assertEqual(output, "foo")