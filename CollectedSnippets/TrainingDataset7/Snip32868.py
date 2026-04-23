def test_date_lazy(self):
        output = self.engine.render_to_string("datelazy", {"t": time(0, 0)})
        self.assertEqual(output, "00:00")