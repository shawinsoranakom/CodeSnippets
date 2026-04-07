def test_validating_multiple_fields(self):
        # There are a couple of ways to do multiple-field validation. If you
        # want the validation message to be associated with a particular field,
        # implement the clean_XXX() method on the Form, where XXX is the field
        # name. As in Field.clean(), the clean_XXX() method should return the
        # cleaned value. In the clean_XXX() method, you have access to
        # self.cleaned_data, which is a dictionary of all the data that has
        # been cleaned *so far*, in order by the fields, including the current
        # field (e.g., the field XXX if you're in clean_XXX()).
        class UserRegistration(Form):
            username = CharField(max_length=10)
            password1 = CharField(widget=PasswordInput)
            password2 = CharField(widget=PasswordInput)

            def clean_password2(self):
                if (
                    self.cleaned_data.get("password1")
                    and self.cleaned_data.get("password2")
                    and self.cleaned_data["password1"] != self.cleaned_data["password2"]
                ):
                    raise ValidationError("Please make sure your passwords match.")

                return self.cleaned_data["password2"]

        f = UserRegistration(auto_id=False)
        self.assertEqual(f.errors, {})
        f = UserRegistration({}, auto_id=False)
        self.assertEqual(f.errors["username"], ["This field is required."])
        self.assertEqual(f.errors["password1"], ["This field is required."])
        self.assertEqual(f.errors["password2"], ["This field is required."])
        f = UserRegistration(
            {"username": "adrian", "password1": "foo", "password2": "bar"},
            auto_id=False,
        )
        self.assertEqual(
            f.errors["password2"], ["Please make sure your passwords match."]
        )
        f = UserRegistration(
            {"username": "adrian", "password1": "foo", "password2": "foo"},
            auto_id=False,
        )
        self.assertEqual(f.errors, {})
        self.assertEqual(f.cleaned_data["username"], "adrian")
        self.assertEqual(f.cleaned_data["password1"], "foo")
        self.assertEqual(f.cleaned_data["password2"], "foo")

        # Another way of doing multiple-field validation is by implementing the
        # Form's clean() method. Usually ValidationError raised by that method
        # will not be associated with a particular field and will have a
        # special-case association with the field named '__all__'. It's
        # possible to associate the errors to particular field with the
        # Form.add_error() method or by passing a dictionary that maps each
        # field to one or more errors.
        #
        # Note that in Form.clean(), you have access to self.cleaned_data, a
        # dictionary of all the fields/values that have *not* raised a
        # ValidationError. Also note Form.clean() is required to return a
        # dictionary of all clean data.
        class UserRegistration(Form):
            username = CharField(max_length=10)
            password1 = CharField(widget=PasswordInput)
            password2 = CharField(widget=PasswordInput)

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

        f = UserRegistration(auto_id=False)
        self.assertEqual(f.errors, {})

        f = UserRegistration({}, auto_id=False)
        self.assertHTMLEqual(
            f.as_table(),
            """<tr><th>Username:</th><td>
<ul class="errorlist"><li>This field is required.</li></ul>
<input type="text" name="username" maxlength="10" aria-invalid="true" required>
</td></tr>
<tr><th>Password1:</th><td><ul class="errorlist"><li>This field is required.</li></ul>
<input type="password" name="password1" aria-invalid="true" required></td></tr>
<tr><th>Password2:</th><td><ul class="errorlist"><li>This field is required.</li></ul>
<input type="password" name="password2" aria-invalid="true" required></td></tr>""",
        )
        self.assertEqual(f.errors["username"], ["This field is required."])
        self.assertEqual(f.errors["password1"], ["This field is required."])
        self.assertEqual(f.errors["password2"], ["This field is required."])

        f = UserRegistration(
            {"username": "adrian", "password1": "foo", "password2": "bar"},
            auto_id=False,
        )
        self.assertEqual(
            f.errors["__all__"], ["Please make sure your passwords match."]
        )
        self.assertHTMLEqual(
            f.as_table(),
            """
            <tr><td colspan="2">
            <ul class="errorlist nonfield">
            <li>Please make sure your passwords match.</li></ul></td></tr>
            <tr><th>Username:</th><td>
            <input type="text" name="username" value="adrian" maxlength="10" required>
            </td></tr>
            <tr><th>Password1:</th><td>
            <input type="password" name="password1" required></td></tr>
            <tr><th>Password2:</th><td>
            <input type="password" name="password2" required></td></tr>
            """,
        )
        self.assertHTMLEqual(
            f.as_ul(),
            """
            <li><ul class="errorlist nonfield">
            <li>Please make sure your passwords match.</li></ul></li>
            <li>Username:
            <input type="text" name="username" value="adrian" maxlength="10" required>
            </li>
            <li>Password1: <input type="password" name="password1" required></li>
            <li>Password2: <input type="password" name="password2" required></li>
            """,
        )
        self.assertHTMLEqual(
            f.render(f.template_name_div),
            '<ul class="errorlist nonfield"><li>Please make sure your passwords match.'
            '</li></ul><div>Username: <input type="text" name="username" '
            'value="adrian" maxlength="10" required></div><div>Password1: <input '
            'type="password" name="password1" required></div><div>Password2: <input '
            'type="password" name="password2" required></div>',
        )

        f = UserRegistration(
            {"username": "adrian", "password1": "foo", "password2": "foo"},
            auto_id=False,
        )
        self.assertEqual(f.errors, {})
        self.assertEqual(f.cleaned_data["username"], "adrian")
        self.assertEqual(f.cleaned_data["password1"], "foo")
        self.assertEqual(f.cleaned_data["password2"], "foo")

        f = UserRegistration(
            {
                "username": "adrian",
                "password1": "FORBIDDEN_VALUE",
                "password2": "FORBIDDEN_VALUE",
            },
            auto_id=False,
        )
        self.assertEqual(f.errors["password1"], ["Forbidden value."])
        self.assertEqual(f.errors["password2"], ["Forbidden value."])

        f = UserRegistration(
            {
                "username": "adrian",
                "password1": "FORBIDDEN_VALUE2",
                "password2": "FORBIDDEN_VALUE2",
            },
            auto_id=False,
        )
        self.assertEqual(
            f.errors["__all__"], ["Non-field error 1.", "Non-field error 2."]
        )
        self.assertEqual(f.errors["password1"], ["Forbidden value 2."])
        self.assertEqual(f.errors["password2"], ["Forbidden value 2."])

        with self.assertRaisesMessage(ValueError, "has no field named"):
            f.add_error("missing_field", "Some error.")

        with self.assertRaisesMessage(
            TypeError,
            "The argument `field` must be `None` when the `error` argument is a "
            "dictionary.",
        ):
            f.add_error("password1", ValidationError({"password1": "Some error."}))