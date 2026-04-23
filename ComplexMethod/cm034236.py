def format_group(group, available_hosts):
            results = {}

            # initialize group + vars
            results[group.name] = {}

            # subgroups
            results[group.name]['children'] = {}
            for subgroup in group.child_groups:
                if subgroup.name != 'all':
                    if subgroup.name in seen_groups:
                        results[group.name]['children'].update({subgroup.name: {}})
                    else:
                        results[group.name]['children'].update(format_group(subgroup, available_hosts))
                        seen_groups.add(subgroup.name)

            # hosts for group
            results[group.name]['hosts'] = {}
            if group.name != 'all':
                for h in group.hosts:
                    if h.name not in available_hosts:
                        continue  # observe limit
                    myvars = {}
                    if h.name not in seen_hosts:  # avoid defining host vars more than once
                        seen_hosts.add(h.name)
                        myvars = self._get_host_variables(host=h)
                    results[group.name]['hosts'][h.name] = myvars

            if context.CLIARGS['export']:
                gvars = self._get_group_variables(group)
                if gvars:
                    results[group.name]['vars'] = gvars

            self._remove_empty_keys(results[group.name])
            # remove empty groups
            if not results[group.name]:
                del results[group.name]

            return results