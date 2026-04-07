def add_arguments(self, parser):
        parser.add_argument("args", metavar=self.label, nargs="+")