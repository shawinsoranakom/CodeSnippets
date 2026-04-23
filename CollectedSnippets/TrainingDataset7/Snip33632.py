def test_for_tag_vars03(self):
        output = self.engine.render_to_string("for-tag-vars03", {"values": [6, 6, 6]})
        self.assertEqual(output, "321")