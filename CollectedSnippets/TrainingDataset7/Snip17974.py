def test_password_validation(self):
        """
        Creation should fail if the password fails validation.
        """
        new_io = StringIO()
        entered_passwords = ["1234567890", "1234567890", "password", "password"]

        def bad_then_good_password():
            return entered_passwords.pop(0)

        @mock_inputs(
            {
                "password": bad_then_good_password,
                "username": "joe1234567890",
                "email": "",
                "bypass": "n",
            }
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
                "This password is entirely numeric.\n"
                "Superuser created successfully.",
            )

        test(self)