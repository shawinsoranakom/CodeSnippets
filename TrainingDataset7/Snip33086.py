def test_time03(self):
        output = self.engine.render_to_string(
            "time03", {"t": time(4, 0, tzinfo=timezone.get_fixed_timezone(30))}
        )
        self.assertEqual(output, "4 a.m.::::")