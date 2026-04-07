def add_arguments(self, parser):
        parser.add_argument(
            "args",
            metavar="fixture",
            nargs="*",
            help="Path(s) to fixtures to load before running the server.",
        )
        parser.add_argument(
            "--noinput",
            "--no-input",
            action="store_false",
            dest="interactive",
            help="Tells Django to NOT prompt the user for input of any kind.",
        )
        parser.add_argument(
            "--addrport",
            default="",
            help="Port number or ipaddr:port to run the server on.",
        )
        parser.add_argument(
            "--ipv6",
            "-6",
            action="store_true",
            dest="use_ipv6",
            help="Tells Django to use an IPv6 address.",
        )