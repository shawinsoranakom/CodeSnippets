def add_arguments(self, parser):
        parser.add_argument(
            "app_label",
            help="App label of the application to optimize the migration for.",
        )
        parser.add_argument(
            "migration_name", help="Migration name to optimize the operations for."
        )
        parser.add_argument(
            "--check",
            action="store_true",
            help="Exit with a non-zero status if the migration can be optimized.",
        )