def test_help_text(self):
        # You can specify descriptive text for a field by using the 'help_text'
        # argument.
        class UserRegistration(Form):
            username = CharField(max_length=10, help_text="e.g., user@example.com")
            password = CharField(
                widget=PasswordInput, help_text="Wählen Sie mit Bedacht."
            )

        p = UserRegistration(auto_id=False)
        self.assertHTMLEqual(
            p.as_ul(),
            """<li>Username: <input type="text" name="username" maxlength="10" required>
<span class="helptext">e.g., user@example.com</span></li>
<li>Password: <input type="password" name="password" required>
<span class="helptext">Wählen Sie mit Bedacht.</span></li>""",
        )
        self.assertHTMLEqual(
            p.as_p(),
            """<p>Username: <input type="text" name="username" maxlength="10" required>
<span class="helptext">e.g., user@example.com</span></p>
<p>Password: <input type="password" name="password" required>
<span class="helptext">Wählen Sie mit Bedacht.</span></p>""",
        )
        self.assertHTMLEqual(
            p.as_table(),
            """
            <tr><th>Username:</th><td>
            <input type="text" name="username" maxlength="10" required><br>
            <span class="helptext">e.g., user@example.com</span></td></tr>
            <tr><th>Password:</th><td><input type="password" name="password" required>
            <br>
            <span class="helptext">Wählen Sie mit Bedacht.</span></td></tr>""",
        )
        self.assertHTMLEqual(
            p.as_div(),
            '<div>Username: <div class="helptext">e.g., user@example.com</div>'
            '<input type="text" name="username" maxlength="10" required></div>'
            '<div>Password: <div class="helptext">Wählen Sie mit Bedacht.</div>'
            '<input type="password" name="password" required></div>',
        )

        # The help text is displayed whether or not data is provided for the
        # form.
        p = UserRegistration({"username": "foo"}, auto_id=False)
        self.assertHTMLEqual(
            p.as_ul(),
            '<li>Username: <input type="text" name="username" value="foo" '
            'maxlength="10" required>'
            '<span class="helptext">e.g., user@example.com</span></li>'
            '<li><ul class="errorlist"><li>This field is required.</li></ul>'
            'Password: <input type="password" name="password" aria-invalid="true" '
            'required><span class="helptext">Wählen Sie mit Bedacht.</span></li>',
        )

        # help_text is not displayed for hidden fields. It can be used for
        # documentation purposes, though.
        class UserRegistration(Form):
            username = CharField(max_length=10, help_text="e.g., user@example.com")
            password = CharField(widget=PasswordInput)
            next = CharField(
                widget=HiddenInput, initial="/", help_text="Redirect destination"
            )

        p = UserRegistration(auto_id=False)
        self.assertHTMLEqual(
            p.as_ul(),
            """<li>Username: <input type="text" name="username" maxlength="10" required>
<span class="helptext">e.g., user@example.com</span></li>
<li>Password: <input type="password" name="password" required>
<input type="hidden" name="next" value="/"></li>""",
        )