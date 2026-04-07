def test_help_text_html_safe(self):
        """help_text should not be escaped."""

        class UserRegistration(Form):
            username = CharField(max_length=10, help_text="e.g., user@example.com")
            password = CharField(
                widget=PasswordInput,
                help_text="Help text is <strong>escaped</strong>.",
            )

        p = UserRegistration(auto_id=False)
        self.assertHTMLEqual(
            p.as_ul(),
            '<li>Username: <input type="text" name="username" maxlength="10" required>'
            '<span class="helptext">e.g., user@example.com</span></li>'
            '<li>Password: <input type="password" name="password" required>'
            '<span class="helptext">Help text is <strong>escaped</strong>.</span></li>',
        )
        self.assertHTMLEqual(
            p.as_p(),
            '<p>Username: <input type="text" name="username" maxlength="10" required>'
            '<span class="helptext">e.g., user@example.com</span></p>'
            '<p>Password: <input type="password" name="password" required>'
            '<span class="helptext">Help text is <strong>escaped</strong>.</span></p>',
        )
        self.assertHTMLEqual(
            p.as_table(),
            "<tr><th>Username:</th><td>"
            '<input type="text" name="username" maxlength="10" required><br>'
            '<span class="helptext">e.g., user@example.com</span></td></tr>'
            "<tr><th>Password:</th><td>"
            '<input type="password" name="password" required><br>'
            '<span class="helptext">Help text is <strong>escaped</strong>.</span>'
            "</td></tr>",
        )