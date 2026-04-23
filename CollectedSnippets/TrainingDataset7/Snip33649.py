def test_for_tag_empty02(self):
        output = self.engine.render_to_string("for-tag-empty02", {"values": []})
        self.assertEqual(output, "values array empty")