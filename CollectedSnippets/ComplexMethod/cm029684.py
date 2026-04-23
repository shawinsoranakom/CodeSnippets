def _get_optional_kwargs(self, *args, **kwargs):
        # determine short and long option strings
        option_strings = []
        for option_string in args:
            # error on strings that don't start with an appropriate prefix
            if option_string[0] not in self.prefix_chars:
                raise ValueError(
                    f'invalid option string {option_string!r}: '
                    f'must start with a character {self.prefix_chars!r}')
            option_strings.append(option_string)

        # infer destination, '--foo-bar' -> 'foo_bar' and '-x' -> 'x'
        dest = kwargs.pop('dest', None)
        if dest is None:
            priority = 0
            for option_string in option_strings:
                if len(option_string) <= 2:
                    # short option: '-x' -> 'x'
                    if priority < 1:
                        dest = option_string.lstrip(self.prefix_chars)
                        priority = 1
                elif option_string[1] not in self.prefix_chars:
                    # single-dash long option: '-foo' -> 'foo'
                    if priority < 2:
                        dest = option_string.lstrip(self.prefix_chars)
                        priority = 2
                else:
                    # two-dash long option: '--foo' -> 'foo'
                    dest = option_string.lstrip(self.prefix_chars)
                    break
            if not dest:
                msg = f'dest= is required for options like {repr(option_strings)[1:-1]}'
                raise TypeError(msg)
            dest = dest.replace('-', '_')

        # return the updated keyword arguments
        return dict(kwargs, dest=dest, option_strings=option_strings)