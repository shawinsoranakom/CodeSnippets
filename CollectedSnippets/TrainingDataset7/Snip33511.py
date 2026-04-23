def test_cycle22(self):
        output = self.engine.render_to_string("cycle22", {"values": [1, 2, 3, 4]})
        self.assertEqual(output, "1234")