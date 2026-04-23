def parse_sources(self, cache=False):
        """ iterate over inventory sources and parse each one to populate it"""

        parsed = False
        # allow for multiple inventory parsing
        for source in self._sources:

            if source:
                if ',' not in source:
                    source = unfrackpath(source, follow=False)
                parse = self.parse_source(source, cache=cache)
                if parse and not parsed:
                    parsed = True

        if parsed:
            # do post processing
            self._inventory.reconcile_inventory()
        else:
            if C.INVENTORY_UNPARSED_IS_FAILED:
                raise AnsibleError("No inventory was parsed, please check your configuration and options.")
            elif C.INVENTORY_UNPARSED_WARNING:
                display.warning("No inventory was parsed, only implicit localhost is available")

        for group in self.groups.values():
            group.vars = combine_vars(group.vars, get_vars_from_inventory_sources(self._loader, self._sources, [group], 'inventory'))
        for host in self.hosts.values():
            host.vars = combine_vars(host.vars, get_vars_from_inventory_sources(self._loader, self._sources, [host], 'inventory'))