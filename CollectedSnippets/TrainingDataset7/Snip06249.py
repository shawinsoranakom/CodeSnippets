def add_arguments(self, parser):
        parser.add_argument(
            "username",
            nargs="?",
            help=(
                "Username to change password for; by default, it's the current "
                "username."
            ),
        )
        parser.add_argument(
            "--database",
            default=DEFAULT_DB_ALIAS,
            choices=tuple(connections),
            help='Specifies the database to use. Default is "default".',
        )