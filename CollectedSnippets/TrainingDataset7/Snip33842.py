def test_invalidstr04_2(self):
        output = self.engine.render_to_string("invalidstr04_2")
        self.assertEqual(output, "Yes")