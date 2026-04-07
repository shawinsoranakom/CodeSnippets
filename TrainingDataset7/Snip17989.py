def test_validation_mismatched_passwords(self):
        """
        Creation should fail if the user enters mismatched passwords.
        """
        new_io = StringIO()

        # The first two passwords do not match, but the second two do match and
        # are valid.
        entered_passwords = ["password", "not password", "password2", "password2"]

        def mismatched_passwords_then_matched():
            return entered_passwords.pop(0)

        @mock_inputs(
            {
                "password": mismatched_passwords_then_matched,
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
                "Error: Your passwords didn't match.\n"
                "Superuser created successfully.",
            )

        test(self)