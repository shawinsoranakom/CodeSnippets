def _get_actions_usage_parts(self, actions, groups):
        """Get usage parts with split index for optionals/positionals.

        Returns (parts, pos_start) where pos_start is the index in parts
        where positionals begin.
        This preserves mutually exclusive group formatting across the
        optionals/positionals boundary (gh-75949).
        """
        actions = [action for action in actions if action.help is not SUPPRESS]
        # group actions by mutually exclusive groups
        action_groups = dict.fromkeys(actions)
        for group in groups:
            for action in group._group_actions:
                if action in action_groups:
                    action_groups[action] = group
        # positional arguments keep their position
        positionals = []
        for action in actions:
            if not action.option_strings:
                group = action_groups.pop(action)
                if group:
                    group_actions = [
                        action2 for action2 in group._group_actions
                        if action2.option_strings and
                           action_groups.pop(action2, None)
                    ] + [action]
                    positionals.append((group.required, group_actions))
                else:
                    positionals.append((None, [action]))
        # the remaining optional arguments are sorted by the position of
        # the first option in the group
        optionals = []
        for action in actions:
            if action.option_strings and action in action_groups:
                group = action_groups.pop(action)
                if group:
                    group_actions = [action] + [
                        action2 for action2 in group._group_actions
                        if action2.option_strings and
                           action_groups.pop(action2, None)
                    ]
                    optionals.append((group.required, group_actions))
                else:
                    optionals.append((None, [action]))

        # collect all actions format strings
        parts = []
        t = self._theme
        pos_start = None
        for i, (required, group) in enumerate(optionals + positionals):
            start = len(parts)
            if i == len(optionals):
                pos_start = start
            in_group = len(group) > 1
            for action in group:
                # produce all arg strings
                if not action.option_strings:
                    default = self._get_default_metavar_for_positional(action)
                    part = self._format_args(action, default)
                    # if it's in a group, strip the outer []
                    if in_group:
                        if part[0] == '[' and part[-1] == ']':
                            part = part[1:-1]
                    part = t.summary_action + part + t.reset

                # produce the first way to invoke the option in brackets
                else:
                    option_string = action.option_strings[0]
                    if self._is_long_option(option_string):
                        option_color = t.summary_long_option
                    else:
                        option_color = t.summary_short_option

                    # if the Optional doesn't take a value, format is:
                    #    -s or --long
                    if action.nargs == 0:
                        part = action.format_usage()
                        part = f"{option_color}{part}{t.reset}"

                    # if the Optional takes a value, format is:
                    #    -s ARGS or --long ARGS
                    else:
                        default = self._get_default_metavar_for_optional(action)
                        args_string = self._format_args(action, default)
                        part = (
                            f"{option_color}{option_string} "
                            f"{t.summary_label}{args_string}{t.reset}"
                        )

                    # make it look optional if it's not required or in a group
                    if not (action.required or required or in_group):
                        part = '[%s]' % part

                # add the action string to the list
                parts.append(part)

            if in_group:
                parts[start] = ('(' if required else '[') + parts[start]
                for i in range(start, len(parts) - 1):
                    parts[i] += ' |'
                parts[-1] += ')' if required else ']'

        if pos_start is None:
            pos_start = len(parts)
        return parts, pos_start