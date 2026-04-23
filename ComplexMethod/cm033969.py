def _execute_meta(self, task: Task, play_context, iterator, target_host: Host):
        task._resolved_action = 'ansible.builtin.meta'  # _post_validate_args is never called for meta actions, so resolved_action hasn't been set

        # meta tasks store their args in the _raw_params field of args,
        # since they do not use k=v pairs, so get that
        meta_action = task._get_meta()

        def _evaluate_conditional(conditional_host: Host) -> bool:
            if not task.when:
                return True

            # FUTURE: If this when fails it will take down the process.
            return task._resolve_conditional(task.when, self._variable_manager.get_vars(
                play=iterator._play, host=conditional_host, task=task, _hosts=self._hosts_cache, _hosts_all=self._hosts_cache_all))

        skipped = False
        msg = meta_action
        skip_reason = '%s conditional evaluated to False' % meta_action
        if isinstance(task, Handler):
            self._tqm.send_callback('v2_playbook_on_handler_task_start', task)
        else:
            self._tqm.send_callback('v2_playbook_on_task_start', task, is_conditional=False)

        # These don't support "when" conditionals
        if meta_action in ('noop', 'refresh_inventory', 'reset_connection') and task.when:
            self._cond_not_supported_warn(meta_action)

        if meta_action == 'noop':
            msg = "noop"
        elif meta_action == 'flush_handlers':
            if _evaluate_conditional(target_host):
                host_state = iterator.get_state_for_host(target_host.name)
                # actually notify proper handlers based on all notifications up to this point
                for notification in list(host_state.handler_notifications):
                    for handler in self.search_handlers_by_notification(notification, iterator):
                        if handler.notify_host(target_host):
                            # NOTE even with notifications deduplicated this can still happen in case of handlers being
                            # notified multiple times using different names, like role name or fqcn
                            self._tqm.send_callback('v2_playbook_on_notify', handler, target_host)
                    iterator.clear_notification(target_host.name, notification)

                if host_state.run_state == IteratingStates.HANDLERS:
                    raise AnsibleError('flush_handlers cannot be used as a handler')
                if target_host.name not in self._tqm._unreachable_hosts:
                    host_state.pre_flushing_run_state = host_state.run_state
                    host_state.run_state = IteratingStates.HANDLERS
                msg = "triggered running handlers for %s" % target_host.name
            else:
                skipped = True
                skip_reason += ', not running handlers for %s' % target_host.name
        elif meta_action == 'refresh_inventory':
            self._inventory.refresh_inventory()
            self._set_hosts_cache(iterator._play)
            msg = "inventory successfully refreshed"
        elif meta_action == 'clear_facts':
            if _evaluate_conditional(target_host):
                for host in self._inventory.get_hosts(iterator._play.hosts):
                    hostname = host.get_name()
                    self._variable_manager.clear_facts(hostname)
                msg = "facts cleared"
            else:
                skipped = True
                skip_reason += ', not clearing facts and fact cache for %s' % target_host.name
        elif meta_action == 'clear_host_errors':
            if _evaluate_conditional(target_host):
                for host in self._inventory.get_hosts(iterator._play.hosts):
                    self._tqm._failed_hosts.pop(host.name, False)
                    self._tqm._unreachable_hosts.pop(host.name, False)
                    iterator.clear_host_errors(host)
                msg = "cleared host errors"
            else:
                skipped = True
                skip_reason += ', not clearing host error state for %s' % target_host.name
        elif meta_action == 'end_batch':
            if _evaluate_conditional(target_host):
                for host in self._inventory.get_hosts(iterator._play.hosts):
                    if host.name not in self._tqm._unreachable_hosts:
                        iterator.end_host(host.name)
                msg = "ending batch"
            else:
                skipped = True
                skip_reason += ', continuing current batch'
        elif meta_action == 'end_play':
            if _evaluate_conditional(target_host):
                for host in self._inventory.get_hosts(iterator._play.hosts):
                    if host.name not in self._tqm._unreachable_hosts:
                        iterator.end_host(host.name)
                        # end_play is used in PlaybookExecutor/TQM to indicate that
                        # the whole play is supposed to be ended as opposed to just a batch
                        iterator.end_play = True
                msg = "ending play"
            else:
                skipped = True
                skip_reason += ', continuing play'
        elif meta_action == 'end_host':
            if _evaluate_conditional(target_host):
                iterator.end_host(target_host.name)
                msg = "ending play for %s" % target_host.name
            else:
                skipped = True
                skip_reason += ", continuing execution for %s" % target_host.name
                # TODO: Nix msg here? Left for historical reasons, but skip_reason exists now.
                msg = "end_host conditional evaluated to false, continuing execution for %s" % target_host.name
        elif meta_action == 'role_complete':
            if task.implicit:
                role_obj = self._get_cached_role(task, iterator._play)
                if target_host.name in role_obj._had_task_run:
                    role_obj._completed[target_host.name] = True
                    msg = 'role_complete for %s' % target_host.name
        elif meta_action == 'end_role':
            if _evaluate_conditional(target_host):
                while True:
                    state, task = iterator.get_next_task_for_host(target_host, peek=True)
                    if task._get_meta() == "role_complete":
                        break
                    iterator.set_state_for_host(target_host.name, state)
                    display.debug("'%s' skipped because role has been ended via 'end_role'" % task)
                msg = 'ending role %s for %s' % (task._role.get_name(), target_host.name)
            else:
                skipped = True
                skip_reason += ', continuing role %s for %s' % (task._role.get_name(), target_host.name)
        elif meta_action == 'reset_connection':
            all_vars = self._variable_manager.get_vars(play=iterator._play, host=target_host, task=task,
                                                       _hosts=self._hosts_cache, _hosts_all=self._hosts_cache_all)
            templar = TemplateEngine(loader=self._loader, variables=all_vars)

            # apply the given task's information to the connection info,
            # which may override some fields already set by the play or
            # the options specified on the command line
            play_context = play_context.set_task_and_variable_override(task=task, variables=all_vars, templar=templar)

            # fields set from the play/task may be based on variables, so we have to
            # do the same kind of post validation step on it here before we use it.
            play_context.post_validate(templar=templar)

            # now that the play context is finalized, if the remote_addr is not set
            # default to using the host's address field as the remote address
            if not play_context.remote_addr:
                play_context.remote_addr = target_host.address

            # We also add "magic" variables back into the variables dict to make sure
            # a certain subset of variables exist. This 'mostly' works here cause meta
            # disregards the loop, but should not really use play_context at all
            play_context.update_vars(all_vars)

            if target_host in self._active_connections:
                connection = Connection(self._active_connections[target_host])
                del self._active_connections[target_host]
            else:
                connection = plugin_loader.connection_loader.get(play_context.connection, play_context, os.devnull)
                var_options = connection._resolve_option_variables(all_vars, templar)
                connection.set_options(task_keys=task.dump_attrs(), var_options=var_options)
                play_context.set_attributes_from_plugin(connection)

            if connection:
                try:
                    connection.reset()
                    msg = 'reset connection'
                except ConnectionError as e:
                    # most likely socket is already closed
                    display.debug("got an error while closing persistent connection: %s" % e)
            else:
                msg = 'no connection, nothing to reset'
        else:
            raise AnsibleError("invalid meta action requested: %s" % meta_action, obj=task._ds)

        utr = _task.UnifiedTaskResult.from_action_result_dict({})
        utr.msg = msg

        if skipped:
            utr.set_skipped(skip_reason)

        header = skip_reason if skipped else msg
        if task.implicit:
            display.debug(f"META: {header}")
        else:
            display.vv(f"META: {header}")

        if skipped:
            self._tqm.send_callback('v2_runner_on_skipped', target_host, task, utr)

        return [HostTaskResult(host=target_host, task=task, utr=utr)]