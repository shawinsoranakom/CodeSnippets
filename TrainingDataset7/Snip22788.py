def test_html_output_with_hidden_input_field_errors(self):
        class TestForm(Form):
            hidden_input = CharField(widget=HiddenInput)

            def clean(self):
                self.add_error(None, "Form error")

        f = TestForm(data={})
        error_dict = {
            "hidden_input": ["This field is required."],
            "__all__": ["Form error"],
        }
        self.assertEqual(f.errors, error_dict)
        f.as_table()
        self.assertEqual(f.errors, error_dict)
        self.assertHTMLEqual(
            f.as_table(),
            '<tr><td colspan="2"><ul class="errorlist nonfield"><li>Form error</li>'
            "<li>(Hidden field hidden_input) This field is required.</li></ul>"
            '<input type="hidden" name="hidden_input" id="id_hidden_input"></td></tr>',
        )
        self.assertHTMLEqual(
            f.as_ul(),
            '<li><ul class="errorlist nonfield"><li>Form error</li>'
            "<li>(Hidden field hidden_input) This field is required.</li></ul>"
            '<input type="hidden" name="hidden_input" id="id_hidden_input"></li>',
        )
        self.assertHTMLEqual(
            f.as_p(),
            '<ul class="errorlist nonfield"><li>Form error</li>'
            "<li>(Hidden field hidden_input) This field is required.</li></ul>"
            '<p><input type="hidden" name="hidden_input" id="id_hidden_input"></p>',
        )
        self.assertHTMLEqual(
            f.render(f.template_name_div),
            '<ul class="errorlist nonfield"><li>Form error</li>'
            "<li>(Hidden field hidden_input) This field is required.</li></ul>"
            '<div><input type="hidden" name="hidden_input" id="id_hidden_input"></div>',
        )