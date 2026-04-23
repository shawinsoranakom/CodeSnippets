def _get_next_task_lockstep(self, hosts: list[Host], iterator: PlayIterator) -> list[tuple[Host, Task]]:
        """
        Returns a list of (host, task) tuples, where the task may
        be a noop task to keep the iterator in lock step across
        all hosts.
        """

        state_task_per_host = {}
        for host in hosts:
            state, task = iterator.get_next_task_for_host(host, peek=True)
            if task is not None:
                state_task_per_host[host] = state, task

        if not state_task_per_host:
            return []

        task_uuids = {t._uuid for s, t in state_task_per_host.values()}
        _loop_cnt = 0
        while _loop_cnt <= 1:
            try:
                cur_task = iterator.all_tasks[iterator.cur_task]
            except IndexError:
                # pick up any tasks left after clear_host_errors
                iterator.cur_task = 0
                _loop_cnt += 1
            else:
                iterator.cur_task += 1
                if cur_task._uuid in task_uuids:
                    break
        else:
            # prevent infinite loop
            raise AnsibleAssertionError(
                'BUG: There seems to be a mismatch between tasks in PlayIterator and HostStates.'
            )

        host_tasks = []
        for host, (state, task) in state_task_per_host.items():
            if cur_task._uuid == task._uuid:
                iterator.set_state_for_host(host.name, state)
                host_tasks.append((host, task))

        if cur_task._get_meta() == 'flush_handlers':
            iterator.all_tasks[iterator.cur_task:iterator.cur_task] = [h for b in iterator._play.handlers for h in b.block]

        return host_tasks