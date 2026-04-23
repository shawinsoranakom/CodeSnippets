def test_update_error_dict(self):
        class CodeForm(Form):
            code = CharField(max_length=10)

            def clean(self):
                try:
                    raise ValidationError({"code": [ValidationError("Code error 1.")]})
                except ValidationError as e:
                    self._errors = e.update_error_dict(self._errors)

                try:
                    raise ValidationError({"code": [ValidationError("Code error 2.")]})
                except ValidationError as e:
                    self._errors = e.update_error_dict(self._errors)

                try:
                    raise ValidationError({"code": ErrorList(["Code error 3."])})
                except ValidationError as e:
                    self._errors = e.update_error_dict(self._errors)

                try:
                    raise ValidationError("Non-field error 1.")
                except ValidationError as e:
                    self._errors = e.update_error_dict(self._errors)

                try:
                    raise ValidationError([ValidationError("Non-field error 2.")])
                except ValidationError as e:
                    self._errors = e.update_error_dict(self._errors)

                # The newly added list of errors is an instance of ErrorList.
                for field, error_list in self._errors.items():
                    if not isinstance(error_list, self.error_class):
                        self._errors[field] = self.error_class(error_list)

        form = CodeForm({"code": "hello"})
        # Trigger validation.
        self.assertFalse(form.is_valid())

        # update_error_dict didn't lose track of the ErrorDict type.
        self.assertIsInstance(form._errors, ErrorDict)

        self.assertEqual(
            dict(form.errors),
            {
                "code": ["Code error 1.", "Code error 2.", "Code error 3."],
                NON_FIELD_ERRORS: ["Non-field error 1.", "Non-field error 2."],
            },
        )