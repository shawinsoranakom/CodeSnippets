def test_createsuperuser_command_with_database_option(self):
        """
        createsuperuser --database should operate on the specified DB.
        """
        new_io = StringIO()
        call_command(
            "createsuperuser",
            interactive=False,
            username="joe",
            email="joe@somewhere.org",
            database="other",
            stdout=new_io,
        )
        command_output = new_io.getvalue().strip()
        self.assertEqual(command_output, "Superuser created successfully.")
        user = User.objects.using("other").get(username="joe")
        self.assertEqual(user.email, "joe@somewhere.org")