def test_form_with_ambiguous_time(self):
        tz = zoneinfo.ZoneInfo("Europe/Paris")
        with timezone.override(tz):
            form = EventForm({"dt": "2011-10-30 02:30:00"})
            self.assertFalse(form.is_valid())
            self.assertEqual(
                form.errors["dt"],
                [
                    "2011-10-30 02:30:00 couldn’t be interpreted in time zone "
                    "Europe/Paris; it may be ambiguous or it may not exist."
                ],
            )