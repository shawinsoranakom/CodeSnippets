def test_validate_password_against_required_fields_via_option(self):
        new_io = StringIO()
        first_name = "josephine"
        entered_passwords = [
            first_name,
            first_name,
            "superduperunguessablepassword",
            "superduperunguessablepassword",
        ]

        def bad_then_good_password():
            return entered_passwords.pop(0)

        @mock_inputs(
            {
                "password": bad_then_good_password,
                "bypass": "n",
            }
        )
        def test(self):
            call_command(
                "createsuperuser",
                interactive=True,
                first_name=first_name,
                date_of_birth="1970-01-01",
                email="joey@example.com",
                stdin=MockTTY(),
                stdout=new_io,
                stderr=new_io,
            )
            self.assertEqual(
                new_io.getvalue().strip(),
                "The password is too similar to the first name.\n"
                "Superuser created successfully.",
            )

        test(self)