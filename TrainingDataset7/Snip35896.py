def add_arguments(self, parser):
        parser.add_argument("integer", nargs="?", type=int, default=0)
        parser.add_argument("-s", "--style", default="Rock'n'Roll")
        parser.add_argument("-x", "--example")
        parser.add_argument("--opt-3", action="store_true", dest="option3")