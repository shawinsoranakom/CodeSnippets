def add_arguments(self, parser):
        parser.add_argument(
            "app_label",
            nargs="?",
            help="App label of an application to synchronize the state.",
        )
        parser.add_argument(
            "migration_name",
            nargs="?",
            help="Database state will be brought to the state after that "
            'migration. Use the name "zero" to unapply all migrations.',
        )
        parser.add_argument(
            "--noinput",
            "--no-input",
            action="store_false",
            dest="interactive",
            help="Tells Django to NOT prompt the user for input of any kind.",
        )
        parser.add_argument(
            "--database",
            default=DEFAULT_DB_ALIAS,
            choices=tuple(connections),
            help=(
                'Nominates a database to synchronize. Defaults to the "default" '
                "database."
            ),
        )
        parser.add_argument(
            "--fake",
            action="store_true",
            help="Mark migrations as run without actually running them.",
        )
        parser.add_argument(
            "--fake-initial",
            action="store_true",
            help=(
                "Detect if tables already exist and fake-apply initial migrations if "
                "so. Make sure that the current database schema matches your initial "
                "migration before using this flag. Django will only check for an "
                "existing table name."
            ),
        )
        parser.add_argument(
            "--plan",
            action="store_true",
            help="Shows a list of the migration actions that will be performed.",
        )
        parser.add_argument(
            "--run-syncdb",
            action="store_true",
            help="Creates tables for apps without migrations.",
        )
        parser.add_argument(
            "--check",
            action="store_true",
            dest="check_unapplied",
            help=(
                "Exits with a non-zero status if unapplied migrations exist and does "
                "not actually apply migrations."
            ),
        )
        parser.add_argument(
            "--prune",
            action="store_true",
            dest="prune",
            help="Delete nonexistent migrations from the django_migrations table.",
        )