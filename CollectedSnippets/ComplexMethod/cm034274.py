def add_dynamic_host(self, host_info: AddHost, already_in_cache: bool = False) -> bool:
        """
        Helper function to add a new host to inventory based on a task result.
        """
        changed = False

        if not already_in_cache:
            self._cached_dynamic_hosts.append(host_info)

        host_name = host_info.host_name

        # Check if host in inventory, add if not
        if host_name not in self.hosts:
            self.add_host(host_name, 'all')
            changed = True

        new_host = self.hosts.get(host_name)

        # Set/update the vars for this host
        new_host_vars = new_host.get_vars()
        new_host_combined_vars = combine_vars(new_host_vars, host_info.host_vars or {})

        if new_host_vars != new_host_combined_vars:
            new_host.vars = new_host_combined_vars
            changed = True

        new_groups = host_info.parent_group_names or []

        for group_name in new_groups:
            if group_name not in self.groups:
                group_name = self._inventory.add_group(group_name)
                changed = True

            new_group = self.groups[group_name]

            if new_group.add_host(self.hosts[host_name]):
                changed = True

        # reconcile inventory, ensures inventory rules are followed
        if changed:
            self.reconcile_inventory()

        return changed