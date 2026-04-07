def test_widthratio07(self):
        """
        71.4 should round to 71
        """
        output = self.engine.render_to_string("widthratio07", {"a": 50, "b": 70})
        self.assertEqual(output, "71")