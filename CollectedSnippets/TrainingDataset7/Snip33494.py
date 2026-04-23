def test_comment_tag04(self):
        output = self.engine.render_to_string("comment-tag04")
        self.assertEqual(output, "foo")