def test_initial_data(self):
        # You can specify initial data for a field by using the 'initial'
        # argument to a Field class. This initial data is displayed when a Form
        # is rendered with *no* data. It is not displayed when a Form is
        # rendered with any data (including an empty dictionary). Also, the
        # initial value is *not* used if data for a particular required field
        # isn't provided.
        class UserRegistration(Form):
            username = CharField(max_length=10, initial="django")
            password = CharField(widget=PasswordInput)

        # Here, we're not submitting any data, so the initial value will be
        # displayed.)
        p = UserRegistration(auto_id=False)
        self.assertHTMLEqual(
            p.as_ul(),
            """
            <li>Username: <input type="text" name="username" value="django"
                maxlength="10" required></li>
            <li>Password: <input type="password" name="password" required></li>
            """,
        )

        # Here, we're submitting data, so the initial value will *not* be
        # displayed.
        p = UserRegistration({}, auto_id=False)
        self.assertHTMLEqual(
            p.as_ul(),
            """<li><ul class="errorlist"><li>This field is required.</li></ul>
Username: <input type="text" name="username" maxlength="10" aria-invalid="true"
required></li><li><ul class="errorlist"><li>This field is required.</li></ul>
Password: <input type="password" name="password" aria-invalid="true" required></li>""",
        )
        p = UserRegistration({"username": ""}, auto_id=False)
        self.assertHTMLEqual(
            p.as_ul(),
            """<li><ul class="errorlist"><li>This field is required.</li></ul>
Username: <input type="text" name="username" maxlength="10" aria-invalid="true"
required></li><li><ul class="errorlist"><li>This field is required.</li></ul>
Password: <input type="password" name="password" aria-invalid="true" required></li>""",
        )
        p = UserRegistration({"username": "foo"}, auto_id=False)
        self.assertHTMLEqual(
            p.as_ul(),
            """
            <li>Username: <input type="text" name="username" value="foo" maxlength="10"
                required></li>
            <li><ul class="errorlist"><li>This field is required.</li></ul>
            Password: <input type="password" name="password" aria-invalid="true"
            required></li>
            """,
        )

        # An 'initial' value is *not* used as a fallback if data is not
        # provided. In this example, we don't provide a value for 'username',
        # and the form raises a validation error rather than using the initial
        # value for 'username'.
        p = UserRegistration({"password": "secret"})
        self.assertEqual(p.errors["username"], ["This field is required."])
        self.assertFalse(p.is_valid())