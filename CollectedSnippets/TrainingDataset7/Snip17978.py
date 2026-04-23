def test_blank_username(self):
        """Creation fails if --username is blank."""
        new_io = StringIO()
        with self.assertRaisesMessage(CommandError, "Username cannot be blank."):
            call_command(
                "createsuperuser",
                username="",
                stdin=MockTTY(),
                stdout=new_io,
                stderr=new_io,
            )