def test_invalidstr03(self):
        output = self.engine.render_to_string("invalidstr03")
        self.assertEqual(output, "")