def test_P_format(self):
        for expected, t in [
            ("midnight", time(0)),
            ("noon", time(12)),
            ("4 a.m.", time(4)),
            ("8:30 a.m.", time(8, 30)),
            ("4 p.m.", time(16)),
            ("8:30 p.m.", time(20, 30)),
        ]:
            with self.subTest(time=t):
                self.assertEqual(dateformat.time_format(t, "P"), expected)