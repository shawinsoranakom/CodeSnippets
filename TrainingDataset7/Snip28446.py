def test_model_clean_error_messages(self):
        data = {"name1": "FORBIDDEN_VALUE", "name2": "ABC"}
        form = CustomErrorMessageForm(data)
        self.assertFalse(form.is_valid())
        self.assertHTMLEqual(
            str(form.errors["name1"]),
            '<ul class="errorlist" id="id_name1_error">'
            "<li>Model.clean() error messages.</li></ul>",
        )
        data = {"name1": "FORBIDDEN_VALUE2", "name2": "ABC"}
        form = CustomErrorMessageForm(data)
        self.assertFalse(form.is_valid())
        self.assertHTMLEqual(
            str(form.errors["name1"]),
            '<ul class="errorlist" id="id_name1_error">'
            "<li>Model.clean() error messages (simpler syntax).</li></ul>",
        )
        data = {"name1": "GLOBAL_ERROR", "name2": "ABC"}
        form = CustomErrorMessageForm(data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["__all__"], ["Global error message."])