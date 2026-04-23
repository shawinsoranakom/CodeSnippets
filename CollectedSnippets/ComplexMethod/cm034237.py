def format_group(group, available_hosts):
            results = {}
            results[group.name] = {}

            results[group.name]['children'] = []
            for subgroup in group.child_groups:
                if subgroup.name == 'ungrouped' and not has_ungrouped:
                    continue
                if group.name != 'all':
                    results[group.name]['children'].append(subgroup.name)
                results.update(format_group(subgroup, available_hosts))

            if group.name != 'all':
                for host in group.hosts:
                    if host.name not in available_hosts:
                        continue
                    if host.name not in seen_hosts:
                        seen_hosts.add(host.name)
                        host_vars = self._get_host_variables(host=host)
                    else:
                        host_vars = {}
                    try:
                        results[group.name]['hosts'][host.name] = host_vars
                    except KeyError:
                        results[group.name]['hosts'] = {host.name: host_vars}

            if context.CLIARGS['export']:
                results[group.name]['vars'] = self._get_group_variables(group)

            self._remove_empty_keys(results[group.name])
            # remove empty groups
            if not results[group.name]:
                del results[group.name]

            return results