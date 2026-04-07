def test_existing_username_non_interactive(self):
        """Creation fails if the username already exists."""
        User.objects.create(username="janet")
        new_io = StringIO()
        with self.assertRaisesMessage(
            CommandError, "Error: That username is already taken."
        ):
            call_command(
                "createsuperuser",
                username="janet",
                email="",
                interactive=False,
                stdout=new_io,
            )