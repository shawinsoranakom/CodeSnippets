def test_for_tag_empty01(self):
        output = self.engine.render_to_string("for-tag-empty01", {"values": [1, 2, 3]})
        self.assertEqual(output, "123")