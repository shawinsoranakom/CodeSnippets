def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--first",
            action="store_false",
            dest="all",
            help="Only return the first match for each static file.",
        )