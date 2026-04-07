def test_existing_username_meta_unique_constraint(self):
        """
        Creation fails if the username already exists and a custom user model
        has UniqueConstraint.
        """
        user = CustomUserWithUniqueConstraint.objects.create(username="janet")
        new_io = StringIO()
        entered_passwords = ["password", "password"]
        # Enter the existing username first and then a new one.
        entered_usernames = [user.username, "joe"]

        def return_passwords():
            return entered_passwords.pop(0)

        def return_usernames():
            return entered_usernames.pop(0)

        @mock_inputs({"password": return_passwords, "username": return_usernames})
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
                "Error: That username is already taken.\n"
                "Superuser created successfully.",
            )

        test(self)