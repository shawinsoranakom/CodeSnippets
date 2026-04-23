def test_form_with_other_timezone(self):
        form = EventForm({"dt": "2011-09-01 17:20:30"})
        with timezone.override(ICT):
            self.assertTrue(form.is_valid())
            self.assertEqual(
                form.cleaned_data["dt"],
                datetime.datetime(2011, 9, 1, 10, 20, 30, tzinfo=UTC),
            )