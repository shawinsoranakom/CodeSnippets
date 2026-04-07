def test_dynamic_initial_data(self):
        # The previous technique dealt with "hard-coded" initial data, but it's
        # also possible to specify initial data after you've already created
        # the Form class (i.e., at runtime). Use the 'initial' parameter to the
        # Form constructor. This should be a dictionary containing initial
        # values for one or more fields in the form, keyed by field name.
        class UserRegistration(Form):
            username = CharField(max_length=10)
            password = CharField(widget=PasswordInput)

        # Here, we're not submitting any data, so the initial value will be
        # displayed.)
        p = UserRegistration(initial={"username": "django"}, auto_id=False)
        self.assertHTMLEqual(
            p.as_ul(),
            """
            <li>Username: <input type="text" name="username" value="django"
                maxlength="10" required></li>
            <li>Password: <input type="password" name="password" required></li>
            """,
        )
        p = UserRegistration(initial={"username": "stephane"}, auto_id=False)
        self.assertHTMLEqual(
            p.as_ul(),
            """
            <li>Username: <input type="text" name="username" value="stephane"
                maxlength="10" required></li>
            <li>Password: <input type="password" name="password" required></li>
            """,
        )

        # The 'initial' parameter is meaningless if you pass data.
        p = UserRegistration({}, initial={"username": "django"}, auto_id=False)
        self.assertHTMLEqual(
            p.as_ul(),
            """<li><ul class="errorlist"><li>This field is required.</li></ul>
Username: <input type="text" name="username" maxlength="10" aria-invalid="true"
required></li><li><ul class="errorlist"><li>This field is required.</li></ul>
Password: <input type="password" name="password" aria-invalid="true" required></li>""",
        )
        p = UserRegistration(
            {"username": ""}, initial={"username": "django"}, auto_id=False
        )
        self.assertHTMLEqual(
            p.as_ul(),
            """<li><ul class="errorlist"><li>This field is required.</li></ul>
Username: <input type="text" name="username" maxlength="10" aria-invalid="true"
required></li><li><ul class="errorlist"><li>This field is required.</li></ul>
Password: <input type="password" name="password" aria-invalid="true" required></li>""",
        )
        p = UserRegistration(
            {"username": "foo"}, initial={"username": "django"}, auto_id=False
        )
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

        # A dynamic 'initial' value is *not* used as a fallback if data is not
        # provided. In this example, we don't provide a value for 'username',
        # and the form raises a validation error rather than using the initial
        # value for 'username'.
        p = UserRegistration({"password": "secret"}, initial={"username": "django"})
        self.assertEqual(p.errors["username"], ["This field is required."])
        self.assertFalse(p.is_valid())

        # If a Form defines 'initial' *and* 'initial' is passed as a parameter
        # to Form(), then the latter will get precedence.
        class UserRegistration(Form):
            username = CharField(max_length=10, initial="django")
            password = CharField(widget=PasswordInput)

        p = UserRegistration(initial={"username": "babik"}, auto_id=False)
        self.assertHTMLEqual(
            p.as_ul(),
            """
            <li>Username: <input type="text" name="username" value="babik"
                maxlength="10" required></li>
            <li>Password: <input type="password" name="password" required></li>
            """,
        )