def test_r_format_with_non_en_locale(self):
        # Changing the locale doesn't change the "r" format.
        dt = datetime(1979, 7, 8, 22, 00)
        with translation.override("fr"):
            self.assertEqual(
                dateformat.format(dt, "r"),
                "Sun, 08 Jul 1979 22:00:00 +0100",
            )