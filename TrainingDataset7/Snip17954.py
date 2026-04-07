def test_validate_username(self):
        msg = (
            "Enter a valid username. This value may contain only letters, numbers, "
            "and @/./+/-/_ characters."
        )
        with self.assertRaisesMessage(CommandError, msg):
            call_command(
                "createsuperuser",
                interactive=False,
                username="🤠",
                email="joe@somewhere.org",
            )