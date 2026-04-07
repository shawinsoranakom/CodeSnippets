def test_blank_email_allowed_non_interactive_environment_variable(self):
        new_io = StringIO()

        call_command(
            "createsuperuser",
            username="joe",
            interactive=False,
            stdout=new_io,
            stderr=new_io,
        )
        self.assertEqual(new_io.getvalue().strip(), "Superuser created successfully.")
        u = User.objects.get(username="joe")
        self.assertEqual(u.email, "")