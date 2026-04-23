def test_blank_username_non_interactive(self):
        new_io = StringIO()
        with self.assertRaisesMessage(CommandError, "Username cannot be blank."):
            call_command(
                "createsuperuser",
                username="",
                interactive=False,
                stdin=MockTTY(),
                stdout=new_io,
                stderr=new_io,
            )