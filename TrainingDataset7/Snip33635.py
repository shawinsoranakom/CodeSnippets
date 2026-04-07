def test_for_tag_vars06(self):
        output = self.engine.render_to_string("for-tag-vars06", {"values": [6, 6, 6]})
        self.assertEqual(output, "xxl")