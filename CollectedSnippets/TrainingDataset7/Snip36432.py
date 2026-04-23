def test_values(self):
        for n, b36 in [(0, "0"), (1, "1"), (42, "16"), (818469960, "django")]:
            self.assertEqual(int_to_base36(n), b36)
            self.assertEqual(base36_to_int(b36), n)