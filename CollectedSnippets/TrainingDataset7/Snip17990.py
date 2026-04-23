def test_validation_blank_password_entered(self):
        """
        Creation should fail if the user enters blank passwords.
        """
        new_io = StringIO()

        # The first two passwords are empty strings, but the second two are
        # valid.
        entered_passwords = ["", "", "password2", "password2"]

        def blank_passwords_then_valid():
            return entered_passwords.pop(0)

        @mock_inputs(
            {
                "password": blank_passwords_then_valid,
                "username": "joe1234567890",
                "email": "",
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
                "Error: Blank passwords aren't allowed.\n"
                "Superuser created successfully.",
            )

        test(self)