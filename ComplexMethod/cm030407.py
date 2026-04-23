def parseArgs(self, argv):
        self._initArgParsers()
        if self.module is None:
            if len(argv) > 1 and argv[1].lower() == 'discover':
                self._do_discovery(argv[2:])
                return
            self._main_parser.parse_args(argv[1:], self)
            if not self.tests:
                # this allows "python -m unittest -v" to still work for
                # test discovery.
                self._do_discovery([])
                return
        else:
            self._main_parser.parse_args(argv[1:], self)

        if self.tests:
            self.testNames = _convert_names(self.tests)
            if __name__ == '__main__':
                # to support python -m unittest ...
                self.module = None
        elif self.defaultTest is None:
            # createTests will load tests from self.module
            self.testNames = None
        elif isinstance(self.defaultTest, str):
            self.testNames = (self.defaultTest,)
        else:
            self.testNames = list(self.defaultTest)
        self.createTests()