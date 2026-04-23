def test_too_many_digits_to_render_very_long(self):
        value = "1" + "0" * 1_000_000
        if PYPY:
            # PyPy casts decimal parts to int, which reaches the integer string
            # conversion length limit (default 4300 digits, CVE-2020-10735).
            with self.assertRaises(ValueError):
                floatformat(value)
        else:
            self.assertEqual(floatformat(value), value)