def parse(self, argv):
        arguments = self._prepare_arguments(argv[1:])
        return self._parser.parse_args(arguments)