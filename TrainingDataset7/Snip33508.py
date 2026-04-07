def test_cycle19(self):
        output = self.engine.render_to_string("cycle19")
        self.assertEqual(output, "ab")