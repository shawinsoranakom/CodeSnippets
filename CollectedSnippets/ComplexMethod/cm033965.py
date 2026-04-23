def run(self, iterator: PlayIterator, play_context: PlayContext, result=0):
        # execute one more pass through the iterator without peeking, to
        # make sure that all of the hosts are advanced to their final task.
        # This should be safe, as everything should be IteratingStates.COMPLETE by
        # this point, though the strategy may not advance the hosts itself.

        for host in self._hosts_cache:
            if host not in self._tqm._unreachable_hosts:
                try:
                    iterator.get_next_task_for_host(self._inventory.hosts[host])
                except KeyError:
                    iterator.get_next_task_for_host(self._inventory.get_host(host))

        # return the appropriate code, depending on the status hosts after the run
        if not isinstance(result, bool) and result != self._tqm.RUN_OK:
            return result
        elif len(self._tqm._unreachable_hosts.keys()) > 0:
            return self._tqm.RUN_UNREACHABLE_HOSTS
        elif len(iterator.get_failed_hosts()) > 0:
            return self._tqm.RUN_FAILED_HOSTS
        else:
            return self._tqm.RUN_OK