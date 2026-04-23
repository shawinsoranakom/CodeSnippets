def add_arguments(self, parser):
        parser.add_argument(
            "--database",
            default=DEFAULT_DB_ALIAS,
            choices=tuple(connections),
            help=(
                "Nominates a database onto which to open a shell. Defaults to the "
                '"default" database.'
            ),
        )
        parameters = parser.add_argument_group("parameters")
        parameters.add_argument("parameters", nargs="*")