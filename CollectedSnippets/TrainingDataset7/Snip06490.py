def add_arguments(self, parser):
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
            help='Nominates the database to use. Defaults to the "default" database.',
        )
        parser.add_argument(
            "--include-stale-apps",
            action="store_true",
            default=False,
            help=(
                "Deletes stale content types including ones from previously "
                "installed apps that have been removed from INSTALLED_APPS."
            ),
        )