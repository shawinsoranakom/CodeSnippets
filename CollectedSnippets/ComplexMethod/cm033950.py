def _add_host_to_composed_groups(self, groups, variables, host, strict=False, fetch_hostvars=True):
        """ helper to create complex groups for plugins based on jinja2 conditionals, hosts that meet the conditional are added to group"""
        # process each 'group entry'
        if groups and isinstance(groups, dict):
            if fetch_hostvars:
                variables = combine_vars(variables, self.inventory.get_host(host).get_vars())
            self.templar.available_variables = variables
            for group_name in groups:
                conditional = groups[group_name]
                group_name = self._sanitize_group_name(group_name)
                try:
                    result = self.templar.evaluate_conditional(conditional)
                except Exception as e:
                    if strict:
                        raise AnsibleParserError("Could not add host %s to group %s: %s" % (host, group_name, to_native(e)))
                    continue

                if result:
                    # ensure group exists, use sanitized name
                    group_name = self.inventory.add_group(group_name)
                    # add host to group
                    self.inventory.add_child(group_name, host)