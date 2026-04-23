def test_datetime_form_initial_data(self):
        class DateTimeRangeForm(forms.Form):
            datetime_field = pg_forms.DateTimeRangeField(show_hidden_initial=True)

        data = QueryDict(mutable=True)
        data.update(
            {
                "datetime_field_0": "2010-01-01 11:13:00",
                "datetime_field_1": "",
                "initial-datetime_field_0": "2010-01-01 10:12:00",
                "initial-datetime_field_1": "",
            }
        )
        form = DateTimeRangeForm(data=data)
        self.assertTrue(form.has_changed())

        data["initial-datetime_field_0"] = "2010-01-01 11:13:00"
        form = DateTimeRangeForm(data=data)
        self.assertFalse(form.has_changed())