def add_arguments(self, parser):
        parser.add_argument(
            "args",
            metavar="test_label",
            nargs="*",
            help=(
                "Module paths to test; can be modulename, modulename.TestCase or "
                "modulename.TestCase.test_method"
            ),
        )
        parser.add_argument(
            "--noinput",
            "--no-input",
            action="store_false",
            dest="interactive",
            help="Tells Django to NOT prompt the user for input of any kind.",
        )
        parser.add_argument(
            "--testrunner",
            help="Tells Django to use specified test runner class instead of "
            "the one specified by the TEST_RUNNER setting.",
        )

        test_runner_class = get_runner(settings, self.test_runner)

        if hasattr(test_runner_class, "add_arguments"):
            test_runner_class.add_arguments(parser)