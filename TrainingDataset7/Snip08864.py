def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--database",
            default=DEFAULT_DB_ALIAS,
            choices=tuple(connections),
            help=(
                'Nominates a database to print the SQL for. Defaults to the "default" '
                "database."
            ),
        )