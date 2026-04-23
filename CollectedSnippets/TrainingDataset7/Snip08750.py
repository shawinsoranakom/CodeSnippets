def add_arguments(self, parser):
        parser.add_argument(
            "--locale",
            "-l",
            action="append",
            default=[],
            help="Locale(s) to process (e.g. de_AT). Default is to process all. "
            "Can be used multiple times.",
        )
        parser.add_argument(
            "--exclude",
            "-x",
            action="append",
            default=[],
            help="Locales to exclude. Default is none. Can be used multiple times.",
        )
        parser.add_argument(
            "--use-fuzzy",
            "-f",
            dest="fuzzy",
            action="store_true",
            help="Use fuzzy translations.",
        )
        parser.add_argument(
            "--ignore",
            "-i",
            action="append",
            dest="ignore_patterns",
            default=[],
            metavar="PATTERN",
            help="Ignore directories matching this glob-style pattern. "
            "Use multiple times to ignore more.",
        )