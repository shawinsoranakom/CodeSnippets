def add_arguments(cls, parser):
        parser.add_argument(
            "--failfast",
            action="store_true",
            help="Stops the test suite after the first failure.",
        )
        parser.add_argument(
            "-t",
            "--top-level-directory",
            dest="top_level",
            help="Top level of project for unittest discovery.",
        )
        parser.add_argument(
            "-p",
            "--pattern",
            default="test*.py",
            help="The test matching pattern. Defaults to test*.py.",
        )
        parser.add_argument(
            "--keepdb", action="store_true", help="Preserves the test DB between runs."
        )
        parser.add_argument(
            "--shuffle",
            nargs="?",
            default=False,
            type=int,
            metavar="SEED",
            help="Shuffles test case order.",
        )
        parser.add_argument(
            "-r",
            "--reverse",
            action="store_true",
            help="Reverses test case order.",
        )
        parser.add_argument(
            "--debug-mode",
            action="store_true",
            help="Sets settings.DEBUG to True.",
        )
        parser.add_argument(
            "-d",
            "--debug-sql",
            action="store_true",
            help="Prints logged SQL queries on failure.",
        )
        parser.add_argument(
            "--parallel",
            nargs="?",
            const="auto",
            default=0,
            type=parallel_type,
            metavar="N",
            help=(
                "Run tests using up to N parallel processes. Use the value "
                '"auto" to run one test process for each processor core.'
            ),
        )
        parser.add_argument(
            "--tag",
            action="append",
            dest="tags",
            help="Run only tests with the specified tag. Can be used multiple times.",
        )
        parser.add_argument(
            "--exclude-tag",
            action="append",
            dest="exclude_tags",
            help="Do not run tests with the specified tag. Can be used multiple times.",
        )
        parser.add_argument(
            "--pdb",
            action="store_true",
            help="Runs a debugger (pdb, or ipdb if installed) on error or failure.",
        )
        parser.add_argument(
            "-b",
            "--buffer",
            action="store_true",
            help="Discard output from passing tests.",
        )
        parser.add_argument(
            "--no-faulthandler",
            action="store_false",
            dest="enable_faulthandler",
            help="Disables the Python faulthandler module during tests.",
        )
        parser.add_argument(
            "--timing",
            action="store_true",
            help=("Output timings, including database set up and total run time."),
        )
        parser.add_argument(
            "-k",
            action="append",
            dest="test_name_patterns",
            help=(
                "Only run test methods and classes that match the pattern "
                "or substring. Can be used multiple times. Same as "
                "unittest -k option."
            ),
        )
        parser.add_argument(
            "--durations",
            dest="durations",
            type=int,
            default=None,
            metavar="N",
            help="Show the N slowest test cases (N=0 for all).",
        )