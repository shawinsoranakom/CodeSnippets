def test_basic_usage(self):
        "Check the operation of the createsuperuser management command"
        # We can use the management command to create a superuser
        new_io = StringIO()
        call_command(
            "createsuperuser",
            interactive=False,
            username="joe",
            email="joe@somewhere.org",
            stdout=new_io,
        )
        command_output = new_io.getvalue().strip()
        self.assertEqual(command_output, "Superuser created successfully.")
        u = User.objects.get(username="joe")
        self.assertEqual(u.email, "joe@somewhere.org")

        # created password should be unusable
        self.assertFalse(u.has_usable_password())