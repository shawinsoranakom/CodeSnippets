def test_date09(self):
        output = self.engine.render_to_string("date09", {"t": time(0, 0)})
        self.assertEqual(output, "00:00")