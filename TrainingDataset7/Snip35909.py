def add_arguments(self, parser):
        parser.add_argument("--foo-list", nargs="+", type=int, required=True)