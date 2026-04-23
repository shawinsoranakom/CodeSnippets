def validate_passwords(
        self,
        password1_field_name="password1",
        password2_field_name="password2",
        usable_password_field_name="usable_password",
    ):
        usable_password = (
            self.cleaned_data.pop(usable_password_field_name, None) != "false"
        )
        self.cleaned_data["set_usable_password"] = usable_password

        if not usable_password:
            return

        password1 = self.cleaned_data.get(password1_field_name)
        password2 = self.cleaned_data.get(password2_field_name)

        if not password1 and password1_field_name not in self.errors:
            error = ValidationError(
                self.fields[password1_field_name].error_messages["required"],
                code="required",
            )
            self.add_error(password1_field_name, error)

        if not password2 and password2_field_name not in self.errors:
            error = ValidationError(
                self.fields[password2_field_name].error_messages["required"],
                code="required",
            )
            self.add_error(password2_field_name, error)

        super().validate_passwords(password1_field_name, password2_field_name)