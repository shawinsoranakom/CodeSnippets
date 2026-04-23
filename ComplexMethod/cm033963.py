def inner(self, iterator: PlayIterator, one_pass: bool = False, max_passes: int | None = None) -> list[HostTaskResult]:
        status_to_stats_map = (
            ('failed', 'failures'),
            ('unreachable', 'dark'),
            ('changed', 'changed'),
            ('skipped', 'skipped'),
        )

        # We don't know the host yet, copy the previous states, for lookup after we process new results
        prev_host_states = iterator.host_states.copy()

        results: list[HostTaskResult] = func(self, iterator, one_pass=one_pass, max_passes=max_passes)
        _processed_results: list[HostTaskResult] = []

        for result in results:
            task = result.task
            host = result.host
            _queued_task_args = self._queued_task_cache.pop((host.name, task._uuid), None)
            task_vars = _queued_task_args['task_vars']
            play_context = _queued_task_args['play_context']
            # Try to grab the previous host state, if it doesn't exist use get_host_state to generate an empty state
            try:
                prev_host_state = prev_host_states[host.name]
            except KeyError:
                prev_host_state = iterator.get_host_state(host)

            while _needs_debugger(task=result.task, utr=result.utr, globally_enabled=self.debugger_active):
                next_action = NextAction()
                dbg = Debugger(task, host, task_vars, play_context, result, next_action)
                dbg.cmdloop()

                if next_action.result == NextAction.REDO:
                    # rollback host state
                    self._tqm.clear_failed_hosts()
                    if task.run_once and iterator._play.strategy in add_internal_fqcns(('linear',)) and result.utr.failed:
                        for host_name, state in prev_host_states.items():
                            if host_name == host.name:
                                continue
                            iterator.set_state_for_host(host_name, state)
                            iterator._play._removed_hosts.remove(host_name)
                    iterator.set_state_for_host(host.name, prev_host_state)
                    for attr, what in status_to_stats_map:
                        if getattr(result.utr, attr):
                            self._tqm._stats.decrement(what, host.name)
                    self._tqm._stats.decrement('ok', host.name)

                    # redo
                    self._queue_task(host, task, task_vars, play_context)

                    _processed_results.extend(debug_closure(func)(self, iterator, one_pass))
                    break
                elif next_action.result == NextAction.CONTINUE:
                    _processed_results.append(result)
                    break
                elif next_action.result == NextAction.EXIT:
                    # Matches KeyboardInterrupt from bin/ansible
                    sys.exit(99)
            else:
                _processed_results.append(result)

        return _processed_results