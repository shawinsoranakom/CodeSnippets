def test_default_timezone_is_zoneinfo(self):
        self.assertIsInstance(timezone.get_default_timezone(), zoneinfo.ZoneInfo)