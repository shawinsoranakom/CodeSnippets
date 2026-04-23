def add_arguments(self, parser):
        parser.add_argument(
            "args",
            metavar="app_label",
            nargs="*",
            help="Specify the app label(s) to works on.",
        )
        parser.add_argument("--empty", action="store_true", help="Do nothing.")