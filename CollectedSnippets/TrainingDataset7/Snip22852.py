def test_error_dict(self):
        class MyForm(Form):
            foo = CharField()
            bar = CharField()

            def clean(self):
                raise ValidationError(
                    "Non-field error.", code="secret", params={"a": 1, "b": 2}
                )

        form = MyForm({})
        self.assertIs(form.is_valid(), False)

        errors = form.errors.as_text()
        control = [
            "* foo\n  * This field is required.",
            "* bar\n  * This field is required.",
            "* __all__\n  * Non-field error.",
        ]
        for error in control:
            self.assertIn(error, errors)

        errors = form.errors.as_ul()
        control = [
            '<li>foo<ul class="errorlist" id="id_foo_error"><li>This field is required.'
            "</li></ul></li>",
            '<li>bar<ul class="errorlist" id="id_bar_error"><li>This field is required.'
            "</li></ul></li>",
            '<li>__all__<ul class="errorlist nonfield"><li>Non-field error.</li></ul>'
            "</li>",
        ]
        for error in control:
            self.assertInHTML(error, errors)

        errors = form.errors.get_json_data()
        control = {
            "foo": [{"code": "required", "message": "This field is required."}],
            "bar": [{"code": "required", "message": "This field is required."}],
            "__all__": [{"code": "secret", "message": "Non-field error."}],
        }
        self.assertEqual(errors, control)
        self.assertEqual(json.dumps(errors), form.errors.as_json())