def _get_option_tuples(self, option_string):
        result = []

        # option strings starting with two prefix characters are only
        # split at the '='
        chars = self.prefix_chars
        if option_string[0] in chars and option_string[1] in chars:
            if self.allow_abbrev:
                option_prefix, sep, explicit_arg = option_string.partition('=')
                if not sep:
                    sep = explicit_arg = None
                for option_string in self._option_string_actions:
                    if option_string.startswith(option_prefix):
                        action = self._option_string_actions[option_string]
                        tup = action, option_string, sep, explicit_arg
                        result.append(tup)

        # single character options can be concatenated with their arguments
        # but multiple character options always have to have their argument
        # separate
        elif option_string[0] in chars and option_string[1] not in chars:
            option_prefix, sep, explicit_arg = option_string.partition('=')
            if not sep:
                sep = explicit_arg = None
            short_option_prefix = option_string[:2]
            short_explicit_arg = option_string[2:]

            for option_string in self._option_string_actions:
                if option_string == short_option_prefix:
                    action = self._option_string_actions[option_string]
                    tup = action, option_string, '', short_explicit_arg
                    result.append(tup)
                elif self.allow_abbrev and option_string.startswith(option_prefix):
                    action = self._option_string_actions[option_string]
                    tup = action, option_string, sep, explicit_arg
                    result.append(tup)

        # shouldn't ever get here
        else:
            raise ArgumentError(None, _('unexpected option string: %s') % option_string)

        # return the collected option tuples
        return result