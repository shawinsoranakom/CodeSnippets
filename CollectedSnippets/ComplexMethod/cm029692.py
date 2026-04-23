def _check_value(self, action, value):
        # converted value must be one of the choices (if specified)
        choices = action.choices
        if choices is None:
            return

        if isinstance(choices, str):
            choices = iter(choices)

        if value not in choices:
            args = {'value': str(value),
                    'choices': ', '.join(map(str, action.choices))}
            msg = _('invalid choice: %(value)r (choose from %(choices)s)')

            if self.suggest_on_error and isinstance(value, str):
                if all(isinstance(choice, str) for choice in action.choices):
                    import difflib
                    suggestions = difflib.get_close_matches(value, action.choices, 1)
                    if suggestions:
                        args['closest'] = suggestions[0]
                        msg = _('invalid choice: %(value)r, maybe you meant %(closest)r? '
                                '(choose from %(choices)s)')

            raise ArgumentError(action, msg % args)