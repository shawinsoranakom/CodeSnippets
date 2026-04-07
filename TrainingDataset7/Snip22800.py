def test_callable_initial_data(self):
        # The previous technique dealt with raw values as initial data, but
        # it's also possible to specify callable data.
        class UserRegistration(Form):
            username = CharField(max_length=10)
            password = CharField(widget=PasswordInput)
            options = MultipleChoiceField(
                choices=[("f", "foo"), ("b", "bar"), ("w", "whiz")]
            )

        # We need to define functions that get called later.)
        def initial_django():
            return "django"

        def initial_stephane():
            return "stephane"

        def initial_options():
            return ["f", "b"]

        def initial_other_options():
            return ["b", "w"]

        # Here, we're not submitting any data, so the initial value will be
        # displayed.)
        p = UserRegistration(
            initial={"username": initial_django, "options": initial_options},
            auto_id=False,
        )
        self.assertHTMLEqual(
            p.as_ul(),
            """
            <li>Username: <input type="text" name="username" value="django"
                maxlength="10" required></li>
            <li>Password: <input type="password" name="password" required></li>
            <li>Options: <select multiple name="options" required>
            <option value="f" selected>foo</option>
            <option value="b" selected>bar</option>
            <option value="w">whiz</option>
            </select></li>
            """,
        )

        # The 'initial' parameter is meaningless if you pass data.
        p = UserRegistration(
            {},
            initial={"username": initial_django, "options": initial_options},
            auto_id=False,
        )
        self.assertHTMLEqual(
            p.as_ul(),
            """<li><ul class="errorlist"><li>This field is required.</li></ul>
Username: <input type="text" name="username" maxlength="10" aria-invalid="true"
required></li><li><ul class="errorlist"><li>This field is required.</li></ul>
Password: <input type="password" name="password" aria-invalid="true"
required></li><li><ul class="errorlist"><li>This field is required.</li></ul>
Options: <select multiple name="options" aria-invalid="true" required>
<option value="f">foo</option>
<option value="b">bar</option>
<option value="w">whiz</option>
</select></li>""",
        )
        p = UserRegistration(
            {"username": ""}, initial={"username": initial_django}, auto_id=False
        )
        self.assertHTMLEqual(
            p.as_ul(),
            """<li><ul class="errorlist"><li>This field is required.</li></ul>
Username: <input type="text" name="username" maxlength="10" aria-invalid="true"
required></li><li><ul class="errorlist"><li>This field is required.</li></ul>
Password: <input type="password" name="password" aria-invalid="true" required></li>
<li><ul class="errorlist"><li>This field is required.</li></ul>
Options: <select multiple name="options" aria-invalid="true" required>
<option value="f">foo</option>
<option value="b">bar</option>
<option value="w">whiz</option>
</select></li>""",
        )
        p = UserRegistration(
            {"username": "foo", "options": ["f", "b"]},
            initial={"username": initial_django},
            auto_id=False,
        )
        self.assertHTMLEqual(
            p.as_ul(),
            """
            <li>Username: <input type="text" name="username" value="foo" maxlength="10"
                required></li>
            <li><ul class="errorlist"><li>This field is required.</li></ul>
            Password: <input type="password" name="password" aria-invalid="true"
            required></li><li>Options: <select multiple name="options" required>
            <option value="f" selected>foo</option>
            <option value="b" selected>bar</option>
            <option value="w">whiz</option>
            </select></li>
            """,
        )

        # A callable 'initial' value is *not* used as a fallback if data is not
        # provided. In this example, we don't provide a value for 'username',
        # and the form raises a validation error rather than using the initial
        # value for 'username'.
        p = UserRegistration(
            {"password": "secret"},
            initial={"username": initial_django, "options": initial_options},
        )
        self.assertEqual(p.errors["username"], ["This field is required."])
        self.assertFalse(p.is_valid())

        # If a Form defines 'initial' *and* 'initial' is passed as a parameter
        # to Form(), then the latter will get precedence.
        class UserRegistration(Form):
            username = CharField(max_length=10, initial=initial_django)
            password = CharField(widget=PasswordInput)
            options = MultipleChoiceField(
                choices=[("f", "foo"), ("b", "bar"), ("w", "whiz")],
                initial=initial_other_options,
            )

        p = UserRegistration(auto_id=False)
        self.assertHTMLEqual(
            p.as_ul(),
            """
            <li>Username: <input type="text" name="username" value="django"
                maxlength="10" required></li>
            <li>Password: <input type="password" name="password" required></li>
            <li>Options: <select multiple name="options" required>
            <option value="f">foo</option>
            <option value="b" selected>bar</option>
            <option value="w" selected>whiz</option>
            </select></li>
            """,
        )
        p = UserRegistration(
            initial={"username": initial_stephane, "options": initial_options},
            auto_id=False,
        )
        self.assertHTMLEqual(
            p.as_ul(),
            """
            <li>Username: <input type="text" name="username" value="stephane"
                maxlength="10" required></li>
            <li>Password: <input type="password" name="password" required></li>
            <li>Options: <select multiple name="options" required>
            <option value="f" selected>foo</option>
            <option value="b" selected>bar</option>
            <option value="w">whiz</option>
            </select></li>
            """,
        )