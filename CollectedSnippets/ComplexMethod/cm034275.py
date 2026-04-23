def add_dynamic_group(self, host_name: str, group_info: AddGroup, already_in_cache: bool = False) -> bool:
        """
        Helper function to add a group (if it does not exist), and to assign the
        specified host to that group.
        """
        changed = False

        if not already_in_cache:
            self._cached_dynamic_grouping.append((host_name, group_info))

        # the host here is from the executor side, which means it was a
        # serialized/cloned copy and we'll need to look up the proper
        # host object from the master inventory
        real_host = self.hosts.get(host_name)

        if real_host is None:
            if host_name == self.localhost.name:
                real_host = self.localhost
            elif not already_in_cache:  # RPFIX-5: BUG: pre-existing issue -- this error check probably needs to happen before mutation has already occurred
                raise AnsibleError('%s cannot be matched in inventory' % host_name)
            else:
                # host was removed from inventory during refresh, we should not process
                return False

        group_name = group_info.group_name

        if group_name not in self.groups:
            group_name = self.add_group(group_name)

        for name in group_info.parent_group_names or []:
            if name not in self.groups:
                # create the new group and add it to inventory
                self.add_group(name)
                changed = True

        group = self._inventory.groups[group_name]

        for parent_group_name in group_info.parent_group_names or []:
            parent_group = self.groups[parent_group_name]
            new = parent_group.add_child_group(group)

            if new and not changed:
                changed = True

        if real_host not in group.get_hosts():
            changed = group.add_host(real_host)

        if group not in real_host.get_groups():
            changed = real_host.add_group(group)

        if changed:
            self.reconcile_inventory()

        return changed