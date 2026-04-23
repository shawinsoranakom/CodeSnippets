def __init__(self,
                 option_strings,
                 dest,
                 default=None,
                 required=False,
                 help=None,
                 deprecated=False):

        _option_strings = []
        neg_option_strings = []
        for option_string in option_strings:
            _option_strings.append(option_string)

            if len(option_string) > 2 and option_string[0] == option_string[1]:
                # two-dash long option: '--foo' -> '--no-foo'
                if option_string.startswith('no-', 2):
                    raise ValueError(f'invalid option name {option_string!r} '
                                     f'for BooleanOptionalAction')
                option_string = option_string[:2] + 'no-' + option_string[2:]
                _option_strings.append(option_string)
                neg_option_strings.append(option_string)
            elif len(option_string) > 2 and option_string[0] != option_string[1]:
                # single-dash long option: '-foo' -> '-nofoo'
                if option_string.startswith('no', 1):
                    raise ValueError(f'invalid option name {option_string!r} '
                                     f'for BooleanOptionalAction')
                option_string = option_string[:1] + 'no' + option_string[1:]
                _option_strings.append(option_string)
                neg_option_strings.append(option_string)

        super().__init__(
            option_strings=_option_strings,
            dest=dest,
            nargs=0,
            default=default,
            required=required,
            help=help,
            deprecated=deprecated)
        self.neg_option_strings = neg_option_strings