def test_custom_error_messages(self):
        data = {"name1": "@#$!!**@#$", "name2": "@#$!!**@#$"}
        errors = CustomErrorMessageForm(data).errors
        self.assertHTMLEqual(
            str(errors["name1"]),
            '<ul class="errorlist" id="id_name1_error">'
            "<li>Form custom error message.</li></ul>",
        )
        self.assertHTMLEqual(
            str(errors["name2"]),
            '<ul class="errorlist" id="id_name2_error">'
            "<li>Model custom error message.</li></ul>",
        )