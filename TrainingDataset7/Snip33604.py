def test_filter01(self):
        output = self.engine.render_to_string("filter01")
        self.assertEqual(output, "")