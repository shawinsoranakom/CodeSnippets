def test_widthratio06(self):
        """
        62.5 should round to 62
        """
        output = self.engine.render_to_string("widthratio06", {"a": 50, "b": 80})
        self.assertEqual(output, "62")