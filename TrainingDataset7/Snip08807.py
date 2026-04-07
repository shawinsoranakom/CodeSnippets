def add_arguments(self, parser):
        parser.add_argument(
            "--locale",
            "-l",
            default=[],
            action="append",
            help=(
                "Creates or updates the message files for the given locale(s) (e.g. "
                "pt_BR). Can be used multiple times."
            ),
        )
        parser.add_argument(
            "--exclude",
            "-x",
            default=[],
            action="append",
            help="Locales to exclude. Default is none. Can be used multiple times.",
        )
        parser.add_argument(
            "--domain",
            "-d",
            default="django",
            help='The domain of the message files (default: "django").',
        )
        parser.add_argument(
            "--all",
            "-a",
            action="store_true",
            help="Updates the message files for all existing locales.",
        )
        parser.add_argument(
            "--extension",
            "-e",
            dest="extensions",
            action="append",
            help='The file extension(s) to examine (default: "html,txt,py", or "js" '
            'if the domain is "djangojs"). Separate multiple extensions with '
            "commas, or use -e multiple times.",
        )
        parser.add_argument(
            "--symlinks",
            "-s",
            action="store_true",
            help="Follows symlinks to directories when examining source code "
            "and templates for translation strings.",
        )
        parser.add_argument(
            "--ignore",
            "-i",
            action="append",
            dest="ignore_patterns",
            default=[],
            metavar="PATTERN",
            help="Ignore files or directories matching this glob-style pattern. "
            "Use multiple times to ignore more.",
        )
        parser.add_argument(
            "--no-default-ignore",
            action="store_false",
            dest="use_default_ignore_patterns",
            help=(
                "Don't ignore the common glob-style patterns 'CVS', '.*', '*~' and "
                "'*.pyc'."
            ),
        )
        parser.add_argument(
            "--no-wrap",
            action="store_true",
            help="Don't break long message lines into several lines.",
        )
        parser.add_argument(
            "--no-location",
            action="store_true",
            help="Don't write '#: filename:line' lines.",
        )
        parser.add_argument(
            "--add-location",
            choices=("full", "file", "never"),
            const="full",
            nargs="?",
            help=(
                "Controls '#: filename:line' lines. If the option is 'full' "
                "(the default if not given), the lines include both file name "
                "and line number. If it's 'file', the line number is omitted. If "
                "it's 'never', the lines are suppressed (same as --no-location). "
                "--add-location requires gettext 0.19 or newer."
            ),
        )
        parser.add_argument(
            "--no-obsolete",
            action="store_true",
            help="Remove obsolete message strings.",
        )
        parser.add_argument(
            "--keep-pot",
            action="store_true",
            help="Keep .pot file after making messages. Useful when debugging.",
        )