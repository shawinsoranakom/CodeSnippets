def test_time00(self):
        output = self.engine.render_to_string("time00", {"dt": time(16, 25)})
        self.assertEqual(output, "4:25 p.m.")