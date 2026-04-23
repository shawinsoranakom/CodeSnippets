def clean(self):
                # Test raising a ValidationError as NON_FIELD_ERRORS.
                if (
                    self.cleaned_data.get("password1")
                    and self.cleaned_data.get("password2")
                    and self.cleaned_data["password1"] != self.cleaned_data["password2"]
                ):
                    raise ValidationError("Please make sure your passwords match.")

                # Test raising ValidationError that targets multiple fields.
                errors = {}
                if self.cleaned_data.get("password1") == "FORBIDDEN_VALUE":
                    errors["password1"] = "Forbidden value."
                if self.cleaned_data.get("password2") == "FORBIDDEN_VALUE":
                    errors["password2"] = ["Forbidden value."]
                if errors:
                    raise ValidationError(errors)

                # Test Form.add_error()
                if self.cleaned_data.get("password1") == "FORBIDDEN_VALUE2":
                    self.add_error(None, "Non-field error 1.")
                    self.add_error("password1", "Forbidden value 2.")
                if self.cleaned_data.get("password2") == "FORBIDDEN_VALUE2":
                    self.add_error("password2", "Forbidden value 2.")
                    raise ValidationError("Non-field error 2.")

                return self.cleaned_data