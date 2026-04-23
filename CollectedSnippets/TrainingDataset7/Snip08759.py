def add_arguments(self, parser):
        parser.add_argument(
            "--all",
            action="store_true",
            help=(
                'Display all settings, regardless of their value. In "hash" '
                'mode, default values are prefixed by "###".'
            ),
        )
        parser.add_argument(
            "--default",
            metavar="MODULE",
            help=(
                "The settings module to compare the current settings against. Leave "
                "empty to compare against Django's default settings."
            ),
        )
        parser.add_argument(
            "--output",
            default="hash",
            choices=("hash", "unified"),
            help=(
                "Selects the output format. 'hash' mode displays each changed "
                "setting, with the settings that don't appear in the defaults "
                "followed by ###. 'unified' mode prefixes the default setting "
                "with a minus sign, followed by the changed setting prefixed "
                "with a plus sign."
            ),
        )