def run(self, tmp=None, task_vars=None):
        """ handler for package operations """

        self._supports_check_mode = True
        self._supports_async = True

        super(ActionModule, self).run(tmp, task_vars)

        module = self._task.args.get('use', 'auto')

        try:
            if module == 'auto':

                if self._task.delegate_to:
                    hosts_vars = task_vars['hostvars'][self._task.delegate_to]
                    tvars = combine_vars(self._task.vars, task_vars.get('delegated_vars', {}))
                else:
                    hosts_vars = task_vars
                    tvars = task_vars

                # use config
                module = tvars.get('ansible_package_use', None)

                if not module:
                    # no use, no config, get from facts
                    if hosts_vars.get('ansible_facts', {}).get('pkg_mgr', False):
                        facts = hosts_vars
                        pmgr = 'pkg_mgr'
                    else:
                        # we had no facts, so generate them
                        # very expensive step, we actually run fact gathering because we don't have facts for this host.
                        facts = self._execute_module(
                            module_name='ansible.legacy.setup',
                            module_args=dict(filter='ansible_pkg_mgr', gather_subset='!all'),
                            task_vars=task_vars,
                        )
                        if facts.get("failed", False):
                            raise AnsibleActionFail(
                                f"Failed to fetch ansible_pkg_mgr to determine the package action backend: {facts.get('msg')}",
                                result=facts,
                            )
                        pmgr = 'ansible_pkg_mgr'

                    try:
                        # actually get from facts
                        module = facts['ansible_facts'][pmgr]
                    except KeyError:
                        raise AnsibleActionFail('Could not detect a package manager. Try using the "use" option.')

            if module and module != 'auto':
                if not self._shared_loader_obj.module_loader.has_plugin(module):
                    raise AnsibleActionFail('Could not find a matching action for the "%s" package manager.' % module)
                else:
                    # run the 'package' module
                    new_module_args = self._task.args.copy()
                    if 'use' in new_module_args:
                        del new_module_args['use']

                    # get defaults for specific module
                    context = self._shared_loader_obj.module_loader.find_plugin_with_context(module, collection_list=self._task.collections)
                    new_module_args = _apply_action_arg_defaults(context.resolved_fqcn, self._task, new_module_args, self._templar)

                    if module in self.BUILTIN_PKG_MGR_MODULES:
                        # prefix with ansible.legacy to eliminate external collisions while still allowing library/ override
                        module = 'ansible.legacy.' + module

                    display.vvvv("Running %s" % module)
                    return self._execute_module(module_name=module, module_args=new_module_args, task_vars=task_vars, wrap_async=self._task.async_val)
            else:
                raise AnsibleActionFail('Could not detect which package manager to use. Try gathering facts or setting the "use" option.')
        finally:
            pass