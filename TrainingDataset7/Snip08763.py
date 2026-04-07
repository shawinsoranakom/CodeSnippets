def add_arguments(self, parser):
        parser.add_argument(
            "args",
            metavar="app_label[.ModelName]",
            nargs="*",
            help=(
                "Restricts dumped data to the specified app_label or "
                "app_label.ModelName."
            ),
        )
        parser.add_argument(
            "--format",
            default="json",
            help="Specifies the output serialization format for fixtures.",
        )
        parser.add_argument(
            "--indent",
            type=int,
            help="Specifies the indent level to use when pretty-printing output.",
        )
        parser.add_argument(
            "--database",
            default=DEFAULT_DB_ALIAS,
            choices=tuple(connections),
            help="Nominates a specific database to dump fixtures from. "
            'Defaults to the "default" database.',
        )
        parser.add_argument(
            "-e",
            "--exclude",
            action="append",
            default=[],
            help="An app_label or app_label.ModelName to exclude "
            "(use multiple --exclude to exclude multiple apps/models).",
        )
        parser.add_argument(
            "--natural-foreign",
            action="store_true",
            dest="use_natural_foreign_keys",
            help="Use natural foreign keys if they are available.",
        )
        parser.add_argument(
            "--natural-primary",
            action="store_true",
            dest="use_natural_primary_keys",
            help="Use natural primary keys if they are available.",
        )
        parser.add_argument(
            "-a",
            "--all",
            action="store_true",
            dest="use_base_manager",
            help=(
                "Use Django's base manager to dump all models stored in the database, "
                "including those that would otherwise be filtered or modified by a "
                "custom manager."
            ),
        )
        parser.add_argument(
            "--pks",
            dest="primary_keys",
            help="Only dump objects with given primary keys. Accepts a comma-separated "
            "list of keys. This option only works when you specify one model.",
        )
        parser.add_argument(
            "-o", "--output", help="Specifies file to which the output is written."
        )