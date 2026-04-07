def test_widget_attrs_custom_aria_describedby(self):
        # aria-describedby provided to the widget overrides the default.

        class UserRegistration(Form):
            username = CharField(
                max_length=255,
                help_text="e.g., user@example.com",
                widget=TextInput(attrs={"aria-describedby": "custom-description"}),
            )
            password = CharField(
                widget=PasswordInput, help_text="Wählen Sie mit Bedacht."
            )

        p = UserRegistration()
        self.assertHTMLEqual(
            p.as_div(),
            '<div><label for="id_username">Username:</label>'
            '<div class="helptext" id="id_username_helptext">e.g., user@example.com'
            '</div><input type="text" name="username" maxlength="255" required '
            'aria-describedby="custom-description" id="id_username">'
            "</div><div>"
            '<label for="id_password">Password:</label>'
            '<div class="helptext" id="id_password_helptext">Wählen Sie mit Bedacht.'
            '</div><input type="password" name="password" required '
            'aria-describedby="id_password_helptext" id="id_password"></div>',
        )
        self.assertHTMLEqual(
            p.as_ul(),
            '<li><label for="id_username">Username:</label><input type="text" '
            'name="username" maxlength="255" required '
            'aria-describedby="custom-description" id="id_username">'
            '<span class="helptext" id="id_username_helptext">e.g., user@example.com'
            "</span></li><li>"
            '<label for="id_password">Password:</label>'
            '<input type="password" name="password" required '
            'aria-describedby="id_password_helptext" id="id_password">'
            '<span class="helptext" id="id_password_helptext">Wählen Sie mit Bedacht.'
            "</span></li>",
        )
        self.assertHTMLEqual(
            p.as_p(),
            '<p><label for="id_username">Username:</label><input type="text" '
            'name="username" maxlength="255" required '
            'aria-describedby="custom-description" id="id_username">'
            '<span class="helptext" id="id_username_helptext">e.g., user@example.com'
            "</span></p><p>"
            '<label for="id_password">Password:</label>'
            '<input type="password" name="password" required '
            'aria-describedby="id_password_helptext" id="id_password">'
            '<span class="helptext" id="id_password_helptext">Wählen Sie mit Bedacht.'
            "</span></p>",
        )
        self.assertHTMLEqual(
            p.as_table(),
            '<tr><th><label for="id_username">Username:</label></th><td>'
            '<input type="text" name="username" maxlength="255" required '
            'aria-describedby="custom-description" id="id_username"><br>'
            '<span class="helptext" id="id_username_helptext">e.g., user@example.com'
            "</span></td></tr><tr><th>"
            '<label for="id_password">Password:</label></th><td>'
            '<input type="password" name="password" required '
            'aria-describedby="id_password_helptext" id="id_password"><br>'
            '<span class="helptext" id="id_password_helptext">Wählen Sie mit Bedacht.'
            "</span></td></tr>",
        )