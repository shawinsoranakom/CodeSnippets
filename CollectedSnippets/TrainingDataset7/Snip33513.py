def test_cycle24(self):
        output = self.engine.render_to_string("cycle24", {"values": [1, 2, 3, 4]})
        self.assertEqual(output, "abca")