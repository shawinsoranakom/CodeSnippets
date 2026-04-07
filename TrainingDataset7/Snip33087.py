def test_time04(self):
        output = self.engine.render_to_string("time04", {"t": time(4, 0)})
        self.assertEqual(output, "4 a.m.::::")