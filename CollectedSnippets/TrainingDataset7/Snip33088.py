def test_time05(self):
        output = self.engine.render_to_string("time05", {"d": self.today})
        self.assertEqual(output, "")