def add_arguments(self, parser):
        parser.add_argument("args", metavar="app_label", nargs="*")
        parser.add_argument(
            "--tag",
            "-t",
            action="append",
            dest="tags",
            help="Run only checks labeled with given tag.",
        )
        parser.add_argument(
            "--list-tags",
            action="store_true",
            help=(
                "List available tags. Specify --deploy to include available deployment "
                "tags."
            ),
        )
        parser.add_argument(
            "--deploy",
            action="store_true",
            help="Check deployment settings.",
        )
        parser.add_argument(
            "--fail-level",
            default="ERROR",
            choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"],
            help=(
                "Message level that will cause the command to exit with a "
                "non-zero status. Default is ERROR."
            ),
        )
        parser.add_argument(
            "--database",
            action="append",
            choices=tuple(connections),
            dest="databases",
            help="Run database related checks against these aliases.",
        )