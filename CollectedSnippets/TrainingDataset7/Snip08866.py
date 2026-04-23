def add_arguments(self, parser):
        parser.add_argument(
            "app_label",
            help="App label of the application to squash migrations for.",
        )
        parser.add_argument(
            "start_migration_name",
            nargs="?",
            help=(
                "Migrations will be squashed starting from and including this "
                "migration."
            ),
        )
        parser.add_argument(
            "migration_name",
            help="Migrations will be squashed until and including this migration.",
        )
        parser.add_argument(
            "--no-optimize",
            action="store_true",
            help="Do not try to optimize the squashed operations.",
        )
        parser.add_argument(
            "--noinput",
            "--no-input",
            action="store_false",
            dest="interactive",
            help="Tells Django to NOT prompt the user for input of any kind.",
        )
        parser.add_argument(
            "--squashed-name",
            help="Sets the name of the new squashed migration.",
        )
        parser.add_argument(
            "--no-header",
            action="store_false",
            dest="include_header",
            help="Do not add a header comment to the new squashed migration.",
        )