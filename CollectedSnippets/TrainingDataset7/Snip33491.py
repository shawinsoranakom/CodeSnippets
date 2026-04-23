def test_comment_tag01(self):
        output = self.engine.render_to_string("comment-tag01")
        self.assertEqual(output, "hello")