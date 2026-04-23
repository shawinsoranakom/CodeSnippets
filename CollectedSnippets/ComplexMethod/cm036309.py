def test_basic(self):
        """
        Tests CPUOffloadingManager with arc policy.
        Verifies that ARC handles store, load, and lookup operations correctly.
        """
        cpu_manager, arc_policy = self._make_manager()

        # prepare store [1, 2]
        prepare_store_output = cpu_manager.prepare_store(
            to_keys([1, 2]), _EMPTY_REQ_CTX
        )
        verify_store_output(
            prepare_store_output,
            ExpectedPrepareStoreOutput(
                keys_to_store=[1, 2],
                store_block_ids=[0, 1],
                evicted_keys=[],
            ),
        )

        # lookup [1, 2] -> not ready
        assert cpu_manager.lookup(to_key(1), _EMPTY_REQ_CTX) is False
        assert cpu_manager.lookup(to_key(2), _EMPTY_REQ_CTX) is False

        # no events so far
        assert list(cpu_manager.take_events()) == []

        # complete store [1, 2]
        cpu_manager.complete_store(to_keys([1, 2]))
        verify_events(cpu_manager.take_events(), expected_stores=({1, 2},))

        # lookup [1, 2]
        assert cpu_manager.lookup(to_key(1), _EMPTY_REQ_CTX) is True
        assert cpu_manager.lookup(to_key(2), _EMPTY_REQ_CTX) is True
        assert cpu_manager.lookup(to_key(3), _EMPTY_REQ_CTX) is False

        # blocks should be in T1 (recent)
        assert len(arc_policy.t1) == 2
        assert len(arc_policy.t2) == 0