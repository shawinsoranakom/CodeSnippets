def test_timezones(self):
        my_birthday = datetime(1979, 7, 8, 22, 00)
        summertime = datetime(2005, 10, 30, 1, 00)
        wintertime = datetime(2005, 10, 30, 4, 00)
        noon = time(12, 0, 0)

        # 3h30m to the west of UTC
        tz = get_fixed_timezone(-210)
        aware_dt = datetime(2009, 5, 16, 5, 30, 30, tzinfo=tz)

        if TZ_SUPPORT:
            for specifier, expected in [
                ("e", ""),
                ("O", "+0100"),
                ("r", "Sun, 08 Jul 1979 22:00:00 +0100"),
                ("T", "CET"),
                ("U", "300315600"),
                ("Z", "3600"),
            ]:
                with self.subTest(specifier=specifier):
                    self.assertEqual(
                        dateformat.format(my_birthday, specifier), expected
                    )

            self.assertEqual(dateformat.format(aware_dt, "e"), "-0330")
            self.assertEqual(
                dateformat.format(aware_dt, "r"),
                "Sat, 16 May 2009 05:30:30 -0330",
            )

            self.assertEqual(dateformat.format(summertime, "I"), "1")
            self.assertEqual(dateformat.format(summertime, "O"), "+0200")

            self.assertEqual(dateformat.format(wintertime, "I"), "0")
            self.assertEqual(dateformat.format(wintertime, "O"), "+0100")

            for specifier in ["e", "O", "T", "Z"]:
                with self.subTest(specifier=specifier):
                    self.assertEqual(dateformat.time_format(noon, specifier), "")

        # Ticket #16924 -- We don't need timezone support to test this
        self.assertEqual(dateformat.format(aware_dt, "O"), "-0330")