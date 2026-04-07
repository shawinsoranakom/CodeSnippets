def add_arguments(self, parser):
        parser.add_argument(
            "args", metavar="fixture", nargs="+", help="Fixture labels."
        )
        parser.add_argument(
            "--database",
            default=DEFAULT_DB_ALIAS,
            choices=tuple(connections),
            help=(
                "Nominates a specific database to load fixtures into. Defaults to the "
                '"default" database.'
            ),
        )
        parser.add_argument(
            "--app",
            dest="app_label",
            help="Only look for fixtures in the specified app.",
        )
        parser.add_argument(
            "--ignorenonexistent",
            "-i",
            action="store_true",
            dest="ignore",
            help="Ignores entries in the serialized data for fields that do not "
            "currently exist on the model.",
        )
        parser.add_argument(
            "-e",
            "--exclude",
            action="append",
            default=[],
            help=(
                "An app_label or app_label.ModelName to exclude. Can be used multiple "
                "times."
            ),
        )
        parser.add_argument(
            "--format",
            help="Format of serialized data when reading from stdin.",
        )