def _add_conflicting_arguments(self):
        """It's too dangerous to use `-y` and `-r` together."""
        group = self._parser.add_mutually_exclusive_group()
        group.add_argument(
            '-y', '--yes', '--yeah', '--hard',
            action='store_true',
            help='execute fixed command without confirmation')
        group.add_argument(
            '-r', '--repeat',
            action='store_true',
            help='repeat on failure')