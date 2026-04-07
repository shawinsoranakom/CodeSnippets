def test_form(self):
        form = EventForm({"dt": "2011-09-01 13:20:30"})
        self.assertTrue(form.is_valid())
        self.assertEqual(
            form.cleaned_data["dt"], datetime.datetime(2011, 9, 1, 13, 20, 30)
        )