def _process_pending_results(self, iterator: PlayIterator, one_pass: bool = False, max_passes: int | None = None) -> list[HostTaskResult]:
        """
        Reads results off the final queue and takes appropriate action
        based on the result (executing callbacks, updating state, etc.).
        """
        ret_results = []
        cur_pass = 0

        while True:
            self._process_rpc_queue()

            try:
                self._results_lock.acquire()
                task_result = self._results.popleft()
            except IndexError:
                break
            finally:
                self._results_lock.release()

            original_host = task_result.host
            original_task: Task = task_result.task

            # all host status messages contain 2 entries: (msg, task_result)
            role_ran = False

            if task_result.utr.failed:
                role_ran = True
                ignore_errors = task_result.utr.ignore_errors

                if not ignore_errors:
                    # save the current state before failing it for later inspection
                    state_when_failed = iterator.get_state_for_host(original_host.name)
                    display.debug("marking %s as failed" % original_host.name)

                    if original_task.run_once:
                        # if we're using run_once, we have to fail every host here
                        for h in self._inventory.get_hosts(iterator._play.hosts):
                            if h.name not in self._tqm._unreachable_hosts:
                                iterator.mark_host_failed(h)
                    else:
                        iterator.mark_host_failed(original_host)

                    state, dummy = iterator.get_next_task_for_host(original_host, peek=True)

                    if iterator.is_failed(original_host) and state and state.run_state == IteratingStates.COMPLETE:
                        self._tqm._failed_hosts[original_host.name] = True

                    # if we're iterating on the rescue portion of a block then
                    # we save the failed task in a special var for use
                    # within the rescue/always
                    if iterator.is_any_block_rescuing(state_when_failed):
                        self._tqm._stats.increment('rescued', original_host.name)

                        iterator._play._removed_hosts.remove(original_host.name)

                        self._variable_manager.set_nonpersistent_facts(
                            original_host.name,
                            dict(
                                ansible_failed_task=original_task.dump_attrs(),
                                ansible_failed_result=task_result.utr.as_result_dict(),
                            ),
                        )
                    else:
                        self._tqm._stats.increment('failures', original_host.name)
                else:
                    self._tqm._stats.increment('ok', original_host.name)
                    self._tqm._stats.increment('ignored', original_host.name)

                    if task_result.utr.changed:
                        self._tqm._stats.increment('changed', original_host.name)

                self._tqm.send_callback('v2_runner_on_failed', task_result, ignore_errors=ignore_errors)
            elif task_result.utr.unreachable:
                if not task_result.utr.ignore_unreachable:
                    self._tqm._unreachable_hosts[original_host.name] = True

                    iterator._play._removed_hosts.append(original_host.name)

                    self._tqm._stats.increment('dark', original_host.name)
                else:
                    self._tqm._stats.increment('ok', original_host.name)
                    self._tqm._stats.increment('ignored', original_host.name)

                self._tqm.send_callback('v2_runner_on_unreachable', task_result)
            elif task_result.utr.skipped:
                self._tqm._stats.increment('skipped', original_host.name)
                self._tqm.send_callback('v2_runner_on_skipped', task_result)
            else:
                role_ran = True

                result_utrs: list[_task.UnifiedTaskResult]

                if original_task.loop:
                    # this task had a loop, and has more than one result, so
                    # loop over all of them instead of a single result
                    result_utrs = task_result.utr.loop_results
                else:
                    result_utrs = [task_result.utr]

                for result_utr in result_utrs:
                    if result_utr.notify and task_result.utr.changed:
                        # only ensure that notified handlers exist, if so save the notifications for when
                        # handlers are actually flushed so the last defined handlers are executed,
                        # otherwise depending on the setting either error or warn
                        host_state = iterator.get_state_for_host(original_host.name)

                        for notification in result_utr.notify:
                            handler: type[Sentinel] | Handler = Sentinel

                            for handler in self.search_handlers_by_notification(notification, iterator):
                                if host_state.run_state == IteratingStates.HANDLERS:
                                    # we're currently iterating handlers, so we need to expand this now
                                    if handler.notify_host(original_host):
                                        # NOTE even with notifications deduplicated this can still happen in case of handlers being
                                        # notified multiple times using different names, like role name or fqcn
                                        self._tqm.send_callback('v2_playbook_on_notify', handler, original_host)
                                else:
                                    iterator.add_notification(original_host.name, notification)
                                    display.vv(f"Notification for handler {notification} has been saved.")
                                    break

                            if handler is Sentinel:
                                msg = (
                                    f"The requested handler '{notification}' was not found in either the main handlers"
                                    " list nor in the listening handlers list"
                                )

                                if C.ERROR_ON_MISSING_HANDLER:
                                    raise AnsibleError(msg)

                                display.warning(msg)

                    if result_utr.pending_changes.register_host_variables:
                        original_host_list = self.get_task_hosts(iterator, original_host, original_task)

                        if original_task.delegate_to and original_task.delegate_facts:
                            potentially_delegated_host_list = [result_utr.delegated_host or original_task.delegate_to]
                        else:
                            potentially_delegated_host_list = original_host_list

                        # Apply changes from register_host_variables to variable manager in sorted order,
                        # to ensure consistent variable precedence based on layer.
                        for variable_layer, variables in sorted(result_utr.pending_changes.register_host_variables.items()):
                            match variable_layer:
                                case _task.VariableLayer.REGISTER_VARS:
                                    for target_host in original_host_list:
                                        self._variable_manager.set_nonpersistent_facts(target_host, variables)
                                case _task.VariableLayer.CACHEABLE_FACT:
                                    for target_host in potentially_delegated_host_list:
                                        self._variable_manager.set_host_facts(target_host, variables)
                                case _task.VariableLayer.EPHEMERAL_FACT:
                                    for target_host in potentially_delegated_host_list:
                                        self._variable_manager.set_nonpersistent_facts(target_host, variables)
                                case _task.VariableLayer.INCLUDE_VARS:
                                    for target_host in potentially_delegated_host_list:
                                        for var_name, var_value in variables.items():
                                            self._variable_manager.set_host_variable(target_host, var_name, var_value)
                                case _:
                                    raise NotSupportedError(f"Unsupported variable layer: {variable_layer}")

                    if result_utr.stats is not None:
                        stats_data = result_utr.stats['data']

                        if result_utr.stats.get('per_host'):
                            host_list = self.get_task_hosts(iterator, original_host, original_task)
                        else:
                            host_list = [None]

                        aggregate = result_utr.stats.get('aggregate')

                        for myhost in host_list:
                            for k in stats_data.keys():
                                if aggregate:
                                    self._tqm._stats.update_custom_stats(k, stats_data[k], myhost)
                                else:
                                    self._tqm._stats.set_custom_stats(k, stats_data[k], myhost)

                if task_result.utr.diff is not None:
                    # this case is only for non-loops; loop item diff callbacks are dispatched directly by TaskExecutor
                    if self._diff or getattr(original_task, 'diff', False):
                        self._tqm.send_callback('v2_on_file_diff', task_result)

                if not isinstance(original_task, TaskInclude):
                    self._tqm._stats.increment('ok', original_host.name)

                    if task_result.utr.changed:
                        self._tqm._stats.increment('changed', original_host.name)

                # finally, send the ok for this task
                self._tqm.send_callback('v2_runner_on_ok', task_result)

            # register final results
            if task_result.utr.registered_values:
                host_list = self.get_task_hosts(iterator, original_host, original_task)

                for target_host in host_list:
                    self._variable_manager.set_nonpersistent_facts(target_host, task_result.utr.registered_values)

            self._pending_results -= 1

            if original_host.name in self._blocked_hosts:
                del self._blocked_hosts[original_host.name]

            # If this is a role task, mark the parent role as being run (if
            # the task was ok or failed, but not skipped or unreachable)
            if original_task._role is not None and role_ran:  # TODO:  and original_task.action not in C._ACTION_INCLUDE_ROLE:?
                # lookup the role in the role cache to make sure we're dealing
                # with the correct object and mark it as executed
                role_obj = self._get_cached_role(original_task, iterator._play)
                role_obj._had_task_run[original_host.name] = True

            ret_results.append(task_result)

            if one_pass or max_passes is not None and (cur_pass + 1) >= max_passes:
                break

            cur_pass += 1

        return ret_results