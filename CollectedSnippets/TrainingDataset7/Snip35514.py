def test_form_with_ambiguous_time(self):
        form = EventForm({"dt": "2011-10-30 02:30:00"})
        tz = zoneinfo.ZoneInfo("Europe/Paris")
        with timezone.override(tz):
            # This is a bug.
            self.assertTrue(form.is_valid())
            self.assertEqual(
                form.cleaned_data["dt"],
                datetime.datetime(2011, 10, 30, 2, 30, 0),
            )