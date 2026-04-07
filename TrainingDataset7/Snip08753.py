def add_arguments(self, parser):
        parser.add_argument(
            "args",
            metavar="table_name",
            nargs="*",
            help=(
                "Optional table names. Otherwise, settings.CACHES is used to find "
                "cache tables."
            ),
        )
        parser.add_argument(
            "--database",
            default=DEFAULT_DB_ALIAS,
            choices=tuple(connections),
            help="Nominates a database onto which the cache tables will be "
            'installed. Defaults to the "default" database.',
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Does not create the table, just prints the SQL that would be run.",
        )