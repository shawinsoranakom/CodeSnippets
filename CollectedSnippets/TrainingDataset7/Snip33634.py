def test_for_tag_vars05(self):
        output = self.engine.render_to_string("for-tag-vars05", {"values": [6, 6, 6]})
        self.assertEqual(output, "fxx")