def test_for_tag_vars02(self):
        output = self.engine.render_to_string("for-tag-vars02", {"values": [6, 6, 6]})
        self.assertEqual(output, "012")