def test_comment_tag02(self):
        output = self.engine.render_to_string("comment-tag02")
        self.assertEqual(output, "hello")