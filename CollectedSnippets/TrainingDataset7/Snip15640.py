def add_arguments(self, parser):
        parser.add_argument("args", nargs="*")
        parser.add_argument("--option_a", "-a", default="1")
        parser.add_argument("--option_b", "-b", default="2")
        parser.add_argument("--option_c", "-c", default="3")