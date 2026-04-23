def test_error_dict_as_json_escape_html(self):
        """#21962 - adding html escape flag to ErrorDict"""

        class MyForm(Form):
            foo = CharField()
            bar = CharField()

            def clean(self):
                raise ValidationError(
                    "<p>Non-field error.</p>",
                    code="secret",
                    params={"a": 1, "b": 2},
                )

        control = {
            "foo": [{"code": "required", "message": "This field is required."}],
            "bar": [{"code": "required", "message": "This field is required."}],
            "__all__": [{"code": "secret", "message": "<p>Non-field error.</p>"}],
        }

        form = MyForm({})
        self.assertFalse(form.is_valid())

        errors = json.loads(form.errors.as_json())
        self.assertEqual(errors, control)

        escaped_error = "&lt;p&gt;Non-field error.&lt;/p&gt;"
        self.assertEqual(
            form.errors.get_json_data(escape_html=True)["__all__"][0]["message"],
            escaped_error,
        )
        errors = json.loads(form.errors.as_json(escape_html=True))
        control["__all__"][0]["message"] = escaped_error
        self.assertEqual(errors, control)