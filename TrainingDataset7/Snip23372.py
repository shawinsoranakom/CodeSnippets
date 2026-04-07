def test_format_value(self):
        valid_formats = [
            "2000-1-1",
            "2000-10-15",
            "2000-01-01",
            "2000-01-0",
            "2000-0-01",
            "2000-0-0",
            "0-01-01",
            "0-01-0",
            "0-0-01",
            "0-0-0",
        ]
        for value in valid_formats:
            year, month, day = (int(x) or "" for x in value.split("-"))
            with self.subTest(value=value):
                self.assertEqual(
                    self.widget.format_value(value),
                    {"day": day, "month": month, "year": year},
                )

        invalid_formats = [
            "2000-01-001",
            "2000-001-01",
            "2-01-01",
            "20-01-01",
            "200-01-01",
            "20000-01-01",
        ]
        for value in invalid_formats:
            with self.subTest(value=value):
                self.assertEqual(
                    self.widget.format_value(value),
                    {"day": None, "month": None, "year": None},
                )