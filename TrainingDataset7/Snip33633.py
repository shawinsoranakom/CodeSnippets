def test_for_tag_vars04(self):
        output = self.engine.render_to_string("for-tag-vars04", {"values": [6, 6, 6]})
        self.assertEqual(output, "210")