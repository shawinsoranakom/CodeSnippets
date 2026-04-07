def test_form_as_table(self):
        class TestForm(Form):
            datetime = SplitDateTimeField()

        f = TestForm()
        self.assertHTMLEqual(
            f.as_table(),
            "<tr><th><label>Datetime:</label></th><td>"
            '<input type="text" name="datetime_0" required id="id_datetime_0">'
            '<input type="text" name="datetime_1" required id="id_datetime_1">'
            "</td></tr>",
        )