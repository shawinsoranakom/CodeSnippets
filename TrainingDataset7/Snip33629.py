def test_for_tag02(self):
        output = self.engine.render_to_string("for-tag02", {"values": [1, 2, 3]})
        self.assertEqual(output, "321")