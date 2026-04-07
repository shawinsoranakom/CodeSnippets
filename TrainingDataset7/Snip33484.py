def test_comment_syntax06(self):
        output = self.engine.render_to_string("comment-syntax06")
        self.assertEqual(output, "foo")