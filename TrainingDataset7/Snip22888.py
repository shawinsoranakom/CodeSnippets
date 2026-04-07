def test_basic_processing_in_view(self):
        class UserRegistration(Form):
            username = CharField(max_length=10)
            password1 = CharField(widget=PasswordInput)
            password2 = CharField(widget=PasswordInput)

            def clean(self):
                if (
                    self.cleaned_data.get("password1")
                    and self.cleaned_data.get("password2")
                    and self.cleaned_data["password1"] != self.cleaned_data["password2"]
                ):
                    raise ValidationError("Please make sure your passwords match.")
                return self.cleaned_data

        def my_function(method, post_data):
            if method == "POST":
                form = UserRegistration(post_data, auto_id=False)
            else:
                form = UserRegistration(auto_id=False)

            if form.is_valid():
                return "VALID: %r" % sorted(form.cleaned_data.items())

            t = Template(
                '<form method="post">'
                "{{ form }}"
                '<input type="submit" required>'
                "</form>"
            )
            return t.render(Context({"form": form}))

        # GET with an empty form and no errors.
        self.assertHTMLEqual(
            my_function("GET", {}),
            '<form method="post">'
            "<div>Username:"
            '<input type="text" name="username" maxlength="10" required></div>'
            "<div>Password1:"
            '<input type="password" name="password1" required></div>'
            "<div>Password2:"
            '<input type="password" name="password2" required></div>'
            '<input type="submit" required>'
            "</form>",
        )
        # POST with erroneous data, a redisplayed form, with errors.
        self.assertHTMLEqual(
            my_function(
                "POST",
                {
                    "username": "this-is-a-long-username",
                    "password1": "foo",
                    "password2": "bar",
                },
            ),
            '<form method="post">'
            '<ul class="errorlist nonfield">'
            "<li>Please make sure your passwords match.</li></ul>"
            '<div>Username:<ul class="errorlist">'
            "<li>Ensure this value has at most 10 characters (it has 23).</li></ul>"
            '<input type="text" name="username" aria-invalid="true" '
            'value="this-is-a-long-username" maxlength="10" required></div>'
            "<div>Password1:"
            '<input type="password" name="password1" required></div>'
            "<div>Password2:"
            '<input type="password" name="password2" required></div>'
            '<input type="submit" required>'
            "</form>",
        )
        # POST with valid data (the success message).
        self.assertEqual(
            my_function(
                "POST",
                {
                    "username": "adrian",
                    "password1": "secret",
                    "password2": "secret",
                },
            ),
            "VALID: [('password1', 'secret'), ('password2', 'secret'), "
            "('username', 'adrian')]",
        )