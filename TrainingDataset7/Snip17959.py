def test_swappable_user_missing_required_field(self):
        """
        A Custom superuser won't be created when a required field isn't
        provided
        """
        # We can use the management command to create a superuser
        # We skip validation because the temporary substitution of the
        # swappable User model messes with validation.
        new_io = StringIO()
        with self.assertRaisesMessage(
            CommandError, "You must use --email with --noinput."
        ):
            call_command(
                "createsuperuser",
                interactive=False,
                stdout=new_io,
                stderr=new_io,
            )

        self.assertEqual(CustomUser._default_manager.count(), 0)