def test_for_tag_vars01(self):
        output = self.engine.render_to_string("for-tag-vars01", {"values": [6, 6, 6]})
        self.assertEqual(output, "123")