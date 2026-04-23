def test_time01(self):
        output = self.engine.render_to_string("time01", {"dt": self.now_tz_i})
        self.assertEqual(output, "+0315:+0315:+0315:11700")