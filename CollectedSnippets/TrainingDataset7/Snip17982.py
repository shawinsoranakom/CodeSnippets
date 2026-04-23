def test_password_validation_bypass(self):
        """
        Password validation can be bypassed by entering 'y' at the prompt.
        """
        new_io = StringIO()

        @mock_inputs(
            {
                "password": "1234567890",
                "username": "joe1234567890",
                "email": "",
                "bypass": "y",
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