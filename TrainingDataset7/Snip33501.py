def test_cycle12(self):
        output = self.engine.render_to_string("cycle12")
        self.assertEqual(output, "abca")