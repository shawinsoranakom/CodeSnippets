def test_datetime_form_as_table(self):
        class DateTimeRangeForm(forms.Form):
            datetime_field = pg_forms.DateTimeRangeField(show_hidden_initial=True)

        form = DateTimeRangeForm()
        self.assertHTMLEqual(
            form.as_table(),
            """
            <tr><th>
            <label>Datetime field:</label>
            </th><td>
            <input type="text" name="datetime_field_0" id="id_datetime_field_0">
            <input type="text" name="datetime_field_1" id="id_datetime_field_1">
            <input type="hidden" name="initial-datetime_field_0"
            id="initial-id_datetime_field_0">
            <input type="hidden" name="initial-datetime_field_1"
            id="initial-id_datetime_field_1">
            </td></tr>
            """,
        )
        form = DateTimeRangeForm(
            {
                "datetime_field_0": "2010-01-01 11:13:00",
                "datetime_field_1": "2020-12-12 16:59:00",
            }
        )
        self.assertHTMLEqual(
            form.as_table(),
            """
            <tr><th>
            <label>Datetime field:</label>
            </th><td>
            <input type="text" name="datetime_field_0"
            value="2010-01-01 11:13:00" id="id_datetime_field_0">
            <input type="text" name="datetime_field_1"
            value="2020-12-12 16:59:00" id="id_datetime_field_1">
            <input type="hidden" name="initial-datetime_field_0"
            value="2010-01-01 11:13:00" id="initial-id_datetime_field_0">
            <input type="hidden" name="initial-datetime_field_1"
            value="2020-12-12 16:59:00" id="initial-id_datetime_field_1"></td></tr>
            """,
        )