def test_load01(self):
        output = self.engine.render_to_string("load01")
        self.assertEqual(output, "test test")