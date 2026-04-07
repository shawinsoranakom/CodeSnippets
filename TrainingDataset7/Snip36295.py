def test_force_bytes_strings_only(self):
        today = datetime.date.today()
        self.assertEqual(force_bytes(today, strings_only=True), today)