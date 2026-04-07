def test_invalid_username(self):
        """Creation fails if the username fails validation."""
        user_field = User._meta.get_field(User.USERNAME_FIELD)
        new_io = StringIO()
        entered_passwords = ["password", "password"]
        # Enter an invalid (too long) username first and then a valid one.
        invalid_username = ("x" * user_field.max_length) + "y"
        entered_usernames = [invalid_username, "janet"]

        def return_passwords():
            return entered_passwords.pop(0)

        def return_usernames():
            return entered_usernames.pop(0)

        @mock_inputs(
            {"password": return_passwords, "username": return_usernames, "email": ""}
        )
        def test(self):
            call_command(
                "createsuperuser",
                interactive=True,
                stdin=MockTTY(),
                stdout=new_io,
                stderr=new_io,
            )
            self.assertEqual(
                new_io.getvalue().strip(),
                "Error: Ensure this value has at most %s characters (it has %s).\n"
                "Superuser created successfully."
                % (user_field.max_length, len(invalid_username)),
            )

        test(self)