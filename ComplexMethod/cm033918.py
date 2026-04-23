def _configure_module(self, module_name, module_args, task_vars) -> tuple[_BuiltModule, str]:
        """
        Handles the loading and templating of the module code through the
        modify_module() function.
        """
        if self._task.delegate_to:
            use_vars = task_vars.get('ansible_delegated_vars')[self._task.delegate_to]
        else:
            use_vars = task_vars

        split_module_name = module_name.split('.')
        collection_name = '.'.join(split_module_name[0:2]) if len(split_module_name) > 2 else ''
        leaf_module_name = resource_from_fqcr(module_name)

        # Search module path(s) for named module.
        for mod_type in self._connection.module_implementation_preferences:
            # Check to determine if PowerShell modules are supported, and apply
            # some fixes (hacks) to module name + args.
            if mod_type == '.ps1':
                # FIXME: This should be temporary and moved to an exec subsystem plugin where we can define the mapping
                # for each subsystem.
                win_collection = 'ansible.windows'
                rewrite_collection_names = ['ansible.builtin', 'ansible.legacy', '']
                # async_status, win_stat, win_file, win_copy, and win_ping are not just like their
                # python counterparts but they are compatible enough for our
                # internal usage
                # NB: we only rewrite the module if it's not being called by the user (eg, an action calling something else)
                # and if it's unqualified or FQ to a builtin
                if leaf_module_name in ('stat', 'file', 'copy', 'ping') and \
                        collection_name in rewrite_collection_names and self._task.action != module_name:
                    module_name = '%s.win_%s' % (win_collection, leaf_module_name)
                elif leaf_module_name == 'async_status' and collection_name in rewrite_collection_names:
                    module_name = '%s.%s' % (win_collection, leaf_module_name)

            result = self._shared_loader_obj.module_loader.find_plugin_with_context(module_name, mod_type, collection_list=self._task.collections)

            if not result.resolved:
                if result.redirect_list and len(result.redirect_list) > 1:
                    # take the last one in the redirect list, we may have successfully jumped through N other redirects
                    target_module_name = result.redirect_list[-1]

                    raise AnsibleError("The module {0} was redirected to {1}, which could not be loaded.".format(module_name, target_module_name))

            module_path = result.plugin_resolved_path
            if module_path:
                break
        else:  # This is a for-else: http://bit.ly/1ElPkyg
            raise AnsibleError("The module %s was not found in configured module paths" % (module_name))

        # insert shared code and arguments into the module
        final_environment: dict[str, t.Any] = {}
        self._compute_environment_string(final_environment)

        # modify_module will exit early if interpreter discovery is required; re-run after if necessary
        for _dummy in (1, 2):
            try:
                module_bits = modify_module(
                    module_name=module_name,
                    module_path=module_path,
                    module_args=module_args,
                    templar=self._templar,
                    task_vars=use_vars,
                    module_compression=C.config.get_config_value('DEFAULT_MODULE_COMPRESSION', variables=task_vars),
                    async_timeout=self._task.async_val,
                    environment=final_environment,
                    remote_is_local=bool(getattr(self._connection, '_remote_is_local', False)),
                    become_plugin=self._connection.become,
                    shell_plugin=self._connection._shell,
                )

                break
            except InterpreterDiscoveryRequiredError as idre:
                self._discovered_interpreter = discover_interpreter(action=self, interpreter_name=idre.interpreter_name,
                                                                    discovery_mode=idre.discovery_mode, task_vars=use_vars)

                # update the local task_vars with the discovered interpreter (which might be None);
                # we'll propagate back to the controller in the task result
                discovered_key = 'discovered_interpreter_%s' % idre.interpreter_name

                # update the local vars copy for the retry
                use_vars['ansible_facts'][discovered_key] = self._discovered_interpreter

                # TODO: this condition prevents 'wrong host' from being updated
                # but in future we would want to be able to update 'delegated host facts'
                # irrespective of task settings
                if not self._task.delegate_to or self._task.delegate_facts:
                    # store in local task_vars facts collection for the retry and any other usages in this worker
                    task_vars['ansible_facts'][discovered_key] = self._discovered_interpreter
                    # preserve this so _execute_module can propagate back to controller as a fact
                    self._discovered_interpreter_key = discovered_key
                else:
                    task_vars['ansible_delegated_vars'][self._task.delegate_to]['ansible_facts'][discovered_key] = self._discovered_interpreter

        return module_bits, module_path