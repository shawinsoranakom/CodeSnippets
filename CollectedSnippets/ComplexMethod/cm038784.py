def format_help(self):
        # Only use custom help formatting for bottom level parsers
        if self._subparsers is not None:
            return super().format_help()

        formatter = self._get_formatter()

        # Handle keyword search of the args
        if (search_keyword := self._search_keyword) is not None:
            # Normalise the search keyword
            search_keyword = search_keyword.lower().replace("_", "-")
            # Return full help if searching for 'all'
            if search_keyword == "all":
                self.epilog = self._json_tip
                return super().format_help()

            # Return group help if searching for a group title
            for group in self._action_groups:
                if group.title and group.title.lower() == search_keyword:
                    formatter.start_section(group.title)
                    formatter.add_text(group.description)
                    formatter.add_arguments(group._group_actions)
                    formatter.end_section()
                    formatter.add_text(self._json_tip)
                    return formatter.format_help()

            # Return matched args if searching for an arg name
            matched_actions = []
            for group in self._action_groups:
                for action in group._group_actions:
                    # search option name
                    if any(
                        search_keyword in opt.lower() for opt in action.option_strings
                    ):
                        matched_actions.append(action)
            if matched_actions:
                formatter.start_section(f"Arguments matching '{search_keyword}'")
                formatter.add_arguments(matched_actions)
                formatter.end_section()
                formatter.add_text(self._json_tip)
                return formatter.format_help()

            # No match found
            formatter.add_text(
                f"No group or arguments matching '{search_keyword}'.\n"
                "Use '--help' to see available groups or "
                "'--help=all' to see all available parameters."
            )
            return formatter.format_help()

        # usage
        formatter.add_usage(self.usage, self._actions, self._mutually_exclusive_groups)

        # description
        formatter.add_text(self.description)

        # positionals, optionals and user-defined groups
        formatter.start_section("Config Groups")
        config_groups = ""
        for group in self._action_groups:
            if not group._group_actions:
                continue
            title = group.title
            description = group.description or ""
            config_groups += f"{title: <24}{description}\n"
        formatter.add_text(config_groups)
        formatter.end_section()

        # epilog
        formatter.add_text(self.epilog)

        # determine help from format above
        return formatter.format_help()