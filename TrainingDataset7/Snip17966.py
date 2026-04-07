def test_validate_fk(self):
        email = Email.objects.create(email="mymail@gmail.com")
        Group.objects.all().delete()
        nonexistent_group_id = 1
        msg = f"group instance with id {nonexistent_group_id!r} is not a valid choice."

        with self.assertRaisesMessage(CommandError, msg):
            call_command(
                "createsuperuser",
                interactive=False,
                username=email.pk,
                email=email.email,
                group=nonexistent_group_id,
                verbosity=0,
            )