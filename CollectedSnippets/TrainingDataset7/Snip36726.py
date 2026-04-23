def test_override_string_tz(self):
        with timezone.override("Asia/Bangkok"):
            self.assertEqual(timezone.get_current_timezone_name(), "Asia/Bangkok")