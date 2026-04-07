def add_arguments(self, parser):
        super().add_arguments(parser)
        self.add_base_argument(parser, "file", nargs="?", help="input file")