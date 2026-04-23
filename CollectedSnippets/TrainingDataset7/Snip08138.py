def add_arguments(self, parser):
        parser.add_argument(
            "--noinput",
            "--no-input",
            action="store_false",
            dest="interactive",
            help="Do NOT prompt the user for input of any kind.",
        )
        parser.add_argument(
            "--no-post-process",
            action="store_false",
            dest="post_process",
            help="Do NOT post process collected files.",
        )
        parser.add_argument(
            "-i",
            "--ignore",
            action="append",
            default=[],
            dest="ignore_patterns",
            metavar="PATTERN",
            help="Ignore files or directories matching this glob-style "
            "pattern. Use multiple times to ignore more.",
        )
        parser.add_argument(
            "-n",
            "--dry-run",
            action="store_true",
            help="Do everything except modify the filesystem.",
        )
        parser.add_argument(
            "-c",
            "--clear",
            action="store_true",
            help="Clear the existing files using the storage "
            "before trying to copy or link the original file.",
        )
        parser.add_argument(
            "-l",
            "--link",
            action="store_true",
            help="Create a symbolic link to each file instead of copying.",
        )
        parser.add_argument(
            "--no-default-ignore",
            action="store_false",
            dest="use_default_ignore_patterns",
            help=(
                "Don't ignore the common private glob-style patterns (defaults to "
                "'CVS', '.*' and '*~')."
            ),
        )