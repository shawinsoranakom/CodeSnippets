def test_time02(self):
        output = self.engine.render_to_string("time02", {"dt": self.now})
        self.assertEqual(output, ":" + self.now_tz.tzinfo.tzname(self.now_tz))