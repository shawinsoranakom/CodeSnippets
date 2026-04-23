def test_load02(self):
        output = self.engine.render_to_string("load02")
        self.assertEqual(output, "test")