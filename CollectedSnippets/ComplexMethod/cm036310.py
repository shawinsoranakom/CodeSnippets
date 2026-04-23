def test_full_scenario(self):
        """
        Comprehensive test covering multiple ARC operations in sequence.
        Similar to the full LRU test but adapted for ARC behavior.
        """
        cpu_manager, arc_policy = self._make_manager()

        # store [1, 2]
        cpu_manager.prepare_store(to_keys([1, 2]), _EMPTY_REQ_CTX)
        cpu_manager.complete_store(to_keys([1, 2]))

        # store [3, 4, 5] -> evicts [1]
        prepare_store_output = cpu_manager.prepare_store(
            to_keys([3, 4, 5]), _EMPTY_REQ_CTX
        )
        assert prepare_store_output is not None
        assert len(prepare_store_output.evicted_keys) == 1
        cpu_manager.complete_store(to_keys([3, 4, 5]))

        # promote some blocks to T2
        cpu_manager.touch(to_keys([2, 3]))

        # T1 has {4, 5}, T2 has {2, 3}
        assert len(arc_policy.t1) == 2
        assert len(arc_policy.t2) == 2

        # store [6] -> should evict from T1 (4 is oldest in T1)
        prepare_store_output = cpu_manager.prepare_store(to_keys([6]), _EMPTY_REQ_CTX)
        assert prepare_store_output is not None
        cpu_manager.complete_store(to_keys([6]))

        # verify blocks 2, 3 (in T2) are still present
        assert cpu_manager.lookup(to_key(2), _EMPTY_REQ_CTX) is True
        assert cpu_manager.lookup(to_key(3), _EMPTY_REQ_CTX) is True

        # verify events
        events = list(cpu_manager.take_events())
        assert len(events) > 0