def test_r_format_with_date(self):
        # Assume midnight in default timezone if datetime.date provided.
        dt = date(2022, 7, 1)
        self.assertEqual(
            dateformat.format(dt, "r"),
            "Fri, 01 Jul 2022 00:00:00 +0200",
        )