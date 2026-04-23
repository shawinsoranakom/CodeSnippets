def test_using_split_datetime_widget(self):
        class SplitDateTimeRangeField(pg_forms.DateTimeRangeField):
            base_field = forms.SplitDateTimeField

        class SplitForm(forms.Form):
            field = SplitDateTimeRangeField()

        form = SplitForm()
        self.assertHTMLEqual(
            str(form),
            """
            <div>
                <fieldset>
                    <legend>Field:</legend>
                    <input id="id_field_0_0" name="field_0_0" type="text">
                    <input id="id_field_0_1" name="field_0_1" type="text">
                    <input id="id_field_1_0" name="field_1_0" type="text">
                    <input id="id_field_1_1" name="field_1_1" type="text">
                </fieldset>
            </div>
        """,
        )
        form = SplitForm(
            {
                "field_0_0": "01/01/2014",
                "field_0_1": "00:00:00",
                "field_1_0": "02/02/2014",
                "field_1_1": "12:12:12",
            }
        )
        self.assertTrue(form.is_valid())
        lower = datetime.datetime(2014, 1, 1, 0, 0, 0)
        upper = datetime.datetime(2014, 2, 2, 12, 12, 12)
        self.assertEqual(form.cleaned_data["field"], DateTimeTZRange(lower, upper))