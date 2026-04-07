def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--nostatic",
            action="store_false",
            dest="use_static_handler",
            help="Tells Django to NOT automatically serve static files at STATIC_URL.",
        )
        parser.add_argument(
            "--insecure",
            action="store_true",
            dest="insecure_serving",
            help="Allows serving static files even if DEBUG is False.",
        )