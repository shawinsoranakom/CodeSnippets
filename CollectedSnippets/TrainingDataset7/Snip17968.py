def test_validate_fk_via_option_interactive(self):
        email = Email.objects.create(email="mymail@gmail.com")
        Group.objects.all().delete()
        nonexistent_group_id = 1
        msg = f"group instance with id {nonexistent_group_id!r} is not a valid choice."

        @mock_inputs(
            {
                "password": "nopasswd",
                "Username (Email.id): ": email.pk,
                "Email (Email.email): ": email.email,
            }
        )
        def test(self):
            with self.assertRaisesMessage(CommandError, msg):
                call_command(
                    "createsuperuser",
                    group=nonexistent_group_id,
                    stdin=MockTTY(),
                    verbosity=0,
                )

        test(self)