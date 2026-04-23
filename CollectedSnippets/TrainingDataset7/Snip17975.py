def test_validate_password_against_username(self):
        new_io = StringIO()
        username = "supremelycomplex"
        entered_passwords = [
            username,
            username,
            "superduperunguessablepassword",
            "superduperunguessablepassword",
        ]

        def bad_then_good_password():
            return entered_passwords.pop(0)

        @mock_inputs(
            {
                "password": bad_then_good_password,
                "username": username,
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
                "The password is too similar to the username.\n"
                "Superuser created successfully.",
            )

        test(self)