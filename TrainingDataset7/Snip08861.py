def add_arguments(self, parser):
        parser.add_argument(
            "app_label", help="App label of the application containing the migration."
        )
        parser.add_argument(
            "migration_name", help="Migration name to print the SQL for."
        )
        parser.add_argument(
            "--database",
            default=DEFAULT_DB_ALIAS,
            choices=tuple(connections),
            help=(
                'Nominates a database to create SQL for. Defaults to the "default" '
                "database."
            ),
        )
        parser.add_argument(
            "--backwards",
            action="store_true",
            help="Creates SQL to unapply the migration, rather than to apply it",
        )