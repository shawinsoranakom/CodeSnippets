def test_cycle10(self):
        output = self.engine.render_to_string("cycle10")
        self.assertEqual(output, "ab")