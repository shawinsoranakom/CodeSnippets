def get_delegated_vars_and_hostname(self, templar, task, variables):
        """Get the delegated_vars for an individual task invocation, which may be in the context
        of an individual loop iteration.

        Not used directly be VariableManager, but used primarily within TaskExecutor
        """
        delegated_vars = {}
        delegated_host_name = ...  # sentinel value distinct from empty/None, which are errors

        if task.delegate_to:
            try:
                delegated_host_name = templar.template(task.delegate_to)
            except AnsibleValueOmittedError:
                pass

        # bypass for unspecified value/omit
        if delegated_host_name is ...:
            return delegated_vars, None

        if not delegated_host_name:
            raise AnsibleError('Empty hostname produced from delegate_to: "%s"' % task.delegate_to)

        delegated_host = self._inventory.get_host(delegated_host_name)
        if delegated_host is None:
            for h in self._inventory.get_hosts(ignore_limits=True, ignore_restrictions=True):
                # check if the address matches, or if both the delegated_to host
                # and the current host are in the list of localhost aliases
                if h.address == delegated_host_name:
                    delegated_host = h
                    break
            else:
                delegated_host = Host(name=delegated_host_name)

        delegated_vars['ansible_delegated_vars'] = {
            delegated_host_name: self.get_vars(
                play=task.get_play(),
                host=delegated_host,
                task=task,
                include_hostvars=True,
            )
        }
        delegated_vars['ansible_delegated_vars'][delegated_host_name]['inventory_hostname'] = variables.get('inventory_hostname')

        return delegated_vars, delegated_host_name