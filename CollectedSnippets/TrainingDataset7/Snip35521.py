def test_split_form(self):
        form = EventSplitForm({"dt_0": "2011-09-01", "dt_1": "13:20:30"})
        self.assertTrue(form.is_valid())
        self.assertEqual(
            form.cleaned_data["dt"],
            datetime.datetime(2011, 9, 1, 10, 20, 30, tzinfo=UTC),
        )