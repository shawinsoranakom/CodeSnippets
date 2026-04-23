def test_get_default_timezone(self):
        self.assertEqual(timezone.get_default_timezone_name(), "America/Chicago")