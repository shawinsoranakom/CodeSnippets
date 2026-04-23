def test_aria_describedby_custom_widget_id(self):
        class UserRegistration(Form):
            username = CharField(
                max_length=255,
                help_text="e.g., user@example.com",
                widget=TextInput(attrs={"id": "custom-id"}),
            )

        f = UserRegistration()
        self.assertHTMLEqual(
            str(f),
            '<div><label for="custom-id">Username:</label>'
            '<div class="helptext" id="id_username_helptext">e.g., user@example.com'
            '</div><input type="text" name="username" id="custom-id" maxlength="255" '
            'required aria-describedby="id_username_helptext"></div>',
        )