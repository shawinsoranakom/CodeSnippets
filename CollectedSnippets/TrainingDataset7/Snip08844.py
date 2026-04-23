def add_arguments(self, parser):
        parser.add_argument(
            "email",
            nargs="*",
            help="One or more email addresses to send a test email to.",
        )
        parser.add_argument(
            "--managers",
            action="store_true",
            help="Send a test email to the addresses specified in settings.MANAGERS.",
        )
        parser.add_argument(
            "--admins",
            action="store_true",
            help="Send a test email to the addresses specified in settings.ADMINS.",
        )