def _add_arguments(self):
        """Adds arguments to parser."""
        self._parser.add_argument(
            '-v', '--version',
            action='store_true',
            help="show program's version number and exit")
        self._parser.add_argument(
            '-a', '--alias',
            nargs='?',
            const=get_alias(),
            help='[custom-alias-name] prints alias for current shell')
        self._parser.add_argument(
            '-l', '--shell-logger',
            action='store',
            help='log shell output to the file')
        self._parser.add_argument(
            '--enable-experimental-instant-mode',
            action='store_true',
            help='enable experimental instant mode, use on your own risk')
        self._parser.add_argument(
            '-h', '--help',
            action='store_true',
            help='show this help message and exit')
        self._add_conflicting_arguments()
        self._parser.add_argument(
            '-d', '--debug',
            action='store_true',
            help='enable debug output')
        self._parser.add_argument(
            '--force-command',
            action='store',
            help=SUPPRESS)
        self._parser.add_argument(
            'command',
            nargs='*',
            help='command that should be fixed')