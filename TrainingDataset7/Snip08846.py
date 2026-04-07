def add_arguments(self, parser):
        parser.add_argument(
            "--no-startup",
            action="store_true",
            help=(
                "When using plain Python, ignore the PYTHONSTARTUP environment "
                "variable and ~/.pythonrc.py script."
            ),
        )
        parser.add_argument(
            "--no-imports",
            action="store_true",
            help="Disable automatic imports of models.",
        )
        parser.add_argument(
            "-i",
            "--interface",
            choices=self.shells,
            help=(
                "Specify an interactive interpreter interface. Available options: "
                '"ipython", "bpython", and "python"'
            ),
        )
        parser.add_argument(
            "-c",
            "--command",
            help=(
                "Instead of opening an interactive shell, run a command as Django and "
                "exit."
            ),
        )