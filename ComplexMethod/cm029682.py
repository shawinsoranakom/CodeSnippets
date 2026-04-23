def add_argument(self, *args, **kwargs):
        """
        add_argument(dest, ..., name=value, ...)
        add_argument(option_string, option_string, ..., name=value, ...)
        """

        # if no positional args are supplied or only one is supplied and
        # it doesn't look like an option string, parse a positional
        # argument
        chars = self.prefix_chars
        if not args or len(args) == 1 and args[0][0] not in chars:
            if args and 'dest' in kwargs:
                raise TypeError('dest supplied twice for positional argument,'
                                ' did you mean metavar?')
            kwargs = self._get_positional_kwargs(*args, **kwargs)

        # otherwise, we're adding an optional argument
        else:
            kwargs = self._get_optional_kwargs(*args, **kwargs)

        # if no default was supplied, use the parser-level default
        if 'default' not in kwargs:
            dest = kwargs['dest']
            if dest in self._defaults:
                kwargs['default'] = self._defaults[dest]
            elif self.argument_default is not None:
                kwargs['default'] = self.argument_default

        # create the action object, and add it to the parser
        action_name = kwargs.get('action')
        action_class = self._pop_action_class(kwargs)
        if not callable(action_class):
            raise ValueError(f'unknown action {action_class!r}')
        action = action_class(**kwargs)

        # raise an error if action for positional argument does not
        # consume arguments
        if not action.option_strings and action.nargs == 0:
            raise ValueError(f'action {action_name!r} is not valid for positional arguments')

        # raise an error if the action type is not callable
        type_func = self._registry_get('type', action.type, action.type)
        if not callable(type_func):
            raise TypeError(f'{type_func!r} is not callable')

        if type_func is FileType:
            raise TypeError(f'{type_func!r} is a FileType class object, '
                            f'instance of it must be passed')

        # raise an error if the metavar does not match the type
        if hasattr(self, "_get_validation_formatter"):
            formatter = self._get_validation_formatter()
            try:
                formatter._format_args(action, None)
            except TypeError:
                raise ValueError("length of metavar tuple does not match nargs")
        self._check_help(action)
        return self._add_action(action)