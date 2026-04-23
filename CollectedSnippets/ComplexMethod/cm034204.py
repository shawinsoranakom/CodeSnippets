def _display_available_roles(self, list_json):
        """Display all roles we can find with a valid argument specification.

        Output is: fqcn role name, entry point, short description
        """
        roles = list(list_json.keys())
        entry_point_names = set()  # to find max len
        for role in roles:
            for entry_point in list_json[role]['entry_points'].keys():
                entry_point_names.add(entry_point)

        max_role_len = 0
        max_ep_len = 0

        if entry_point_names:
            max_ep_len = max(len(x) for x in entry_point_names)

        linelimit = display.columns - max_role_len - max_ep_len - 5
        text = []

        for role in sorted(roles):
            if list_json[role]['entry_points']:
                text.append('%s:' % role)
                text.append('  specs:')
                for entry_point, desc in list_json[role]['entry_points'].items():
                    if len(desc) > linelimit:
                        desc = desc[:linelimit] + '...'
                    text.append("    %-*s: %s" % (max_ep_len, entry_point, desc))
            else:
                text.append('%s' % role)

        # display results
        DocCLI.pager("\n".join(text))