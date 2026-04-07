def add_arguments(self, parser):
        parser.add_argument("name", help="Name of the application or project.")
        parser.add_argument(
            "directory",
            nargs="?",
            help="Optional destination directory, this will be created if needed.",
        )
        parser.add_argument(
            "--template", help="The path or URL to load the template from."
        )
        parser.add_argument(
            "--extension",
            "-e",
            dest="extensions",
            action="append",
            default=["py"],
            help='The file extension(s) to render (default: "py"). '
            "Separate multiple extensions with commas, or use "
            "-e multiple times.",
        )
        parser.add_argument(
            "--name",
            "-n",
            dest="files",
            action="append",
            default=[],
            help="The file name(s) to render. Separate multiple file names "
            "with commas, or use -n multiple times.",
        )
        parser.add_argument(
            "--exclude",
            "-x",
            action="append",
            default=argparse.SUPPRESS,
            nargs="?",
            const="",
            help=(
                "The directory name(s) to exclude, in addition to .git and "
                "__pycache__. Can be used multiple times."
            ),
        )