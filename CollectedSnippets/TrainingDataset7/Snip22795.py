def test_form_html_attributes(self):
        # Some Field classes have an effect on the HTML attributes of their
        # associated Widget. If you set max_length in a CharField and its
        # associated widget is either a TextInput or PasswordInput, then the
        # widget's rendered HTML will include the "maxlength" attribute.
        class UserRegistration(Form):
            username = CharField(max_length=10)  # uses TextInput by default
            password = CharField(max_length=10, widget=PasswordInput)
            realname = CharField(
                max_length=10, widget=TextInput
            )  # redundantly define widget, just to test
            address = CharField()  # no max_length defined here

        p = UserRegistration(auto_id=False)
        self.assertHTMLEqual(
            p.as_ul(),
            """
            <li>Username: <input type="text" name="username" maxlength="10" required>
            </li>
            <li>Password: <input type="password" name="password" maxlength="10"
                required></li>
            <li>Realname: <input type="text" name="realname" maxlength="10" required>
            </li>
            <li>Address: <input type="text" name="address" required></li>
            """,
        )

        # If you specify a custom "attrs" that includes the "maxlength"
        # attribute, the Field's max_length attribute will override whatever
        # "maxlength" you specify in "attrs".
        class UserRegistration(Form):
            username = CharField(
                max_length=10, widget=TextInput(attrs={"maxlength": 20})
            )
            password = CharField(max_length=10, widget=PasswordInput)

        p = UserRegistration(auto_id=False)
        self.assertHTMLEqual(
            p.as_ul(),
            '<li>Username: <input type="text" name="username" maxlength="10" required>'
            "</li>"
            '<li>Password: <input type="password" name="password" maxlength="10" '
            "required></li>",
        )