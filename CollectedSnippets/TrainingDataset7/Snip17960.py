def test_swappable_user_username_non_unique(self):
        @mock_inputs(
            {
                "username": "joe",
                "password": "nopasswd",
            }
        )
        def createsuperuser():
            new_io = StringIO()
            call_command(
                "createsuperuser",
                interactive=True,
                email="joe@somewhere.org",
                stdout=new_io,
                stdin=MockTTY(),
            )
            command_output = new_io.getvalue().strip()
            self.assertEqual(command_output, "Superuser created successfully.")

        for i in range(2):
            createsuperuser()

        users = CustomUserNonUniqueUsername.objects.filter(username="joe")
        self.assertEqual(users.count(), 2)