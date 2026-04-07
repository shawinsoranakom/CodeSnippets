def test_existing_username_provided_via_option_and_interactive(self):
        """call_command() gets username='janet' and interactive=True."""
        new_io = StringIO()
        entered_passwords = ["password", "password"]
        User.objects.create(username="janet")

        def return_passwords():
            return entered_passwords.pop(0)

        @mock_inputs(
            {
                "password": return_passwords,
                "username": "janet1",
                "email": "test@test.com",
            }
        )
        def test(self):
            call_command(
                "createsuperuser",
                username="janet",
                interactive=True,
                stdin=MockTTY(),
                stdout=new_io,
                stderr=new_io,
            )
            msg = (
                "Error: That username is already taken.\n"
                "Superuser created successfully."
            )
            self.assertEqual(new_io.getvalue().strip(), msg)

        test(self)