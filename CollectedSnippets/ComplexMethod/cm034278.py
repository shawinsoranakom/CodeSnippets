def reconcile_inventory(self) -> None:
        """Ensure inventory basic rules, run after updates."""

        display.debug('Reconcile groups and hosts in inventory.')
        self.current_source = None

        group_names = set()
        # set group vars from group_vars/ files and vars plugins
        for g in self.groups:
            group = self.groups[g]
            group_names.add(group.name)

            # ensure all groups inherit from 'all'
            if group.name != 'all' and not group.get_ancestors():
                self.add_child('all', group.name)

        host_names = set()
        # get host vars from host_vars/ files and vars plugins
        for host in self.hosts.values():
            host_names.add(host.name)

            mygroups = host.get_groups()

            if self.groups['ungrouped'] in mygroups:
                # clear ungrouped of any incorrectly stored by parser
                if set(mygroups).difference({self.groups['all'], self.groups['ungrouped']}):
                    self.groups['ungrouped'].remove_host(host)

            elif not host.implicit:
                # add ungrouped hosts to ungrouped, except implicit
                length = len(mygroups)
                if length == 0 or (length == 1 and self.groups['all'] in mygroups):
                    self.add_child('ungrouped', host.name)

            # special case for implicit hosts
            if host.implicit:
                host.vars = combine_vars(self.groups['all'].get_vars(), host.vars)

        # warn if overloading identifier as both group and host
        for conflict in group_names.intersection(host_names):
            display.warning("Found both group and host with same name: %s" % conflict)

        self._groups_dict_cache = {}