def test_date08(self):
        output = self.engine.render_to_string("date08", {"t": time(0, 1)})
        self.assertEqual(output, "00:01")