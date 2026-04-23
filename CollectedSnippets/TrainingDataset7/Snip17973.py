def test_default_username(self):
        """createsuperuser uses a default username when one isn't provided."""
        # Get the default username before creating a user.
        default_username = get_default_username()
        new_io = StringIO()
        entered_passwords = ["password", "password"]

        def return_passwords():
            return entered_passwords.pop(0)

        @mock_inputs({"password": return_passwords, "username": "", "email": ""})
        def test(self):
            call_command(
                "createsuperuser",
                interactive=True,
                stdin=MockTTY(),
                stdout=new_io,
                stderr=new_io,
            )
            self.assertEqual(
                new_io.getvalue().strip(), "Superuser created successfully."
            )
            self.assertTrue(User.objects.filter(username=default_username).exists())

        test(self)