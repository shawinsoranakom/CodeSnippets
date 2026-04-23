def test_form_with_non_existent_time(self):
        form = EventForm({"dt": "2011-03-27 02:30:00"})
        tz = zoneinfo.ZoneInfo("Europe/Paris")
        with timezone.override(tz):
            # This is a bug.
            self.assertTrue(form.is_valid())
            self.assertEqual(
                form.cleaned_data["dt"],
                datetime.datetime(2011, 3, 27, 2, 30, 0),
            )