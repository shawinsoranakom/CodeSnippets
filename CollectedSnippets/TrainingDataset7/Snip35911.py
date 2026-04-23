def add_arguments(self, parser):
        parser.add_argument("-n", "--need-me", required=True)
        parser.add_argument("-t", "--need-me-too", required=True, dest="needme2")