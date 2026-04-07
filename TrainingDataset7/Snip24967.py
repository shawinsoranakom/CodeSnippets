def test_no_option(self):
        # One of either the --locale, --exclude, or --all options is required.
        msg = "Type 'manage.py help makemessages' for usage information."
        with mock.patch(
            "django.core.management.commands.makemessages.sys.argv",
            ["manage.py", "makemessages"],
        ):
            with self.assertRaisesRegex(CommandError, msg):
                management.call_command("makemessages")