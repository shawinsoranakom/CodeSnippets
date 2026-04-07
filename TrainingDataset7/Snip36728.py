def test_activate_invalid_timezone(self):
        with self.assertRaisesMessage(ValueError, "Invalid timezone: None"):
            timezone.activate(None)