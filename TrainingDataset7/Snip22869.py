def test_only_hidden_fields(self):
        # A form with *only* hidden fields that has errors is going to be very
        # unusual.
        class HiddenForm(Form):
            data = IntegerField(widget=HiddenInput)

        f = HiddenForm({})
        self.assertHTMLEqual(
            f.as_p(),
            '<ul class="errorlist nonfield">'
            "<li>(Hidden field data) This field is required.</li></ul>\n<p> "
            '<input type="hidden" name="data" id="id_data"></p>',
        )
        self.assertHTMLEqual(
            f.as_table(),
            '<tr><td colspan="2"><ul class="errorlist nonfield">'
            "<li>(Hidden field data) This field is required.</li></ul>"
            '<input type="hidden" name="data" id="id_data"></td></tr>',
        )