def test_cycle23(self):
        output = self.engine.render_to_string("cycle23", {"values": [1, 2, 3, 4]})
        self.assertEqual(output, "a1b2c3a4")