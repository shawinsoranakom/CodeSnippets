def test_verbosity_zero(self):
        # We can suppress output on the management command
        new_io = StringIO()
        call_command(
            "createsuperuser",
            interactive=False,
            username="joe2",
            email="joe2@somewhere.org",
            verbosity=0,
            stdout=new_io,
        )
        command_output = new_io.getvalue().strip()
        self.assertEqual(command_output, "")
        u = User.objects.get(username="joe2")
        self.assertEqual(u.email, "joe2@somewhere.org")
        self.assertFalse(u.has_usable_password())