def format_group(group, available_hosts):
            results = {}
            results[group.name] = {}
            if group.name != 'all':
                results[group.name]['hosts'] = [h.name for h in group.hosts if h.name in available_hosts]
            results[group.name]['children'] = []
            for subgroup in group.child_groups:
                results[group.name]['children'].append(subgroup.name)
                if subgroup.name not in seen_groups:
                    results.update(format_group(subgroup, available_hosts))
                    seen_groups.add(subgroup.name)
            if context.CLIARGS['export']:
                results[group.name]['vars'] = self._get_group_variables(group)

            self._remove_empty_keys(results[group.name])
            # remove empty groups
            if not results[group.name]:
                del results[group.name]

            return results