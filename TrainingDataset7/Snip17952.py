def test_no_email_argument(self):
        new_io = StringIO()
        with self.assertRaisesMessage(
            CommandError, "You must use --email with --noinput."
        ):
            call_command(
                "createsuperuser", interactive=False, username="joe", stdout=new_io
            )