def _parse(self, lines):
        """
        Populates self.groups from the given array of lines. Raises an error on
        any parse failure.
        """

        self._compile_patterns()

        # We behave as though the first line of the inventory is '[ungrouped]',
        # and begin to look for host definitions. We make a single pass through
        # each line of the inventory, building up self.groups and adding hosts,
        # subgroups, and setting variables as we go.

        pending_declarations = {}
        groupname = 'ungrouped'
        state = 'hosts'
        for line in lines:
            self._origin = self._origin.replace(line_num=self._origin.line_num + 1)

            line = line.strip()
            # Skip empty lines and comments
            if not line or line[0] in self._COMMENT_MARKERS:
                continue

            # Is this a [section] header? That tells us what group we're parsing
            # definitions for, and what kind of definitions to expect.

            m = self.patterns['section'].match(line)
            if m:
                (groupname, state) = m.groups()

                groupname = to_safe_group_name(groupname)

                state = state or 'hosts'
                if state not in ['hosts', 'children', 'vars']:
                    title = ":".join(m.groups())
                    self._raise_error("Section [%s] has unknown type: %s" % (title, state))

                # If we haven't seen this group before, we add a new Group.
                if groupname not in self.inventory.groups:
                    # Either [groupname] or [groupname:children] is sufficient to declare a group,
                    # but [groupname:vars] is allowed only if the # group is declared elsewhere.
                    # We add the group anyway, but make a note in pending_declarations to check at the end.
                    #
                    # It's possible that a group is previously pending due to being defined as a child
                    # group, in that case we simply pass so that the logic below to process pending
                    # declarations will take the appropriate action for a pending child group instead of
                    # incorrectly handling it as a var state pending declaration
                    if state == 'vars' and groupname not in pending_declarations:
                        pending_declarations[groupname] = dict(line=self._origin.line_num, state=state, name=groupname)

                    self.inventory.add_group(groupname)

                # When we see a declaration that we've been waiting for, we process and delete.
                if groupname in pending_declarations and state != 'vars':
                    if pending_declarations[groupname]['state'] == 'children':
                        self._add_pending_children(groupname, pending_declarations)
                    elif pending_declarations[groupname]['state'] == 'vars':
                        del pending_declarations[groupname]

                continue
            elif line.startswith('[') and line.endswith(']'):
                self._raise_error("Invalid section entry: '%s'. Please make sure that there are no spaces" % line + " " +
                                  "in the section entry, and that there are no other invalid characters")

            # It's not a section, so the current state tells us what kind of
            # definition it must be. The individual parsers will raise an
            # error if we feed them something they can't digest.

            # [groupname] contains host definitions that must be added to
            # the current group.
            if state == 'hosts':
                hosts, port, variables = self._parse_host_definition(line)
                self._populate_host_vars(hosts, variables, groupname, port)

            # [groupname:vars] contains variable definitions that must be
            # applied to the current group.
            elif state == 'vars':
                (k, v) = self._parse_variable_definition(line)
                self.inventory.set_variable(groupname, k, v)

            # [groupname:children] contains subgroup names that must be
            # added as children of the current group. The subgroup names
            # must themselves be declared as groups, but as before, they
            # may only be declared later.
            elif state == 'children':
                child = self._parse_group_name(line)
                if child not in self.inventory.groups:
                    if child not in pending_declarations:
                        pending_declarations[child] = dict(line=self._origin.line_num, state=state, name=child, parents=[groupname])
                    else:
                        pending_declarations[child]['parents'].append(groupname)
                else:
                    self.inventory.add_child(groupname, child)
            else:
                # This can happen only if the state checker accepts a state that isn't handled above.
                self._raise_error("Entered unhandled state: %s" % (state))

        # Any entries in pending_declarations not removed by a group declaration above mean that there was an unresolved reference.
        # We report only the first such error here.
        for g in pending_declarations:
            decl = pending_declarations[g]
            self._origin = self._origin.replace(line_num=decl['line'])
            if decl['state'] == 'vars':
                raise ValueError(f"Section [{decl['name']}:vars] not valid for undefined group {decl['name']!r}.")
            elif decl['state'] == 'children':
                raise ValueError(f"Section [{decl['parents'][-1]}:children] includes undefined group {decl['name']!r}.")