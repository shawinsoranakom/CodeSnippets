def test_failure_in_setUpTestData_should_rollback_transaction(self):
        # setUpTestData() should call _rollback_atomics() so that the
        # transaction doesn't leak.
        self.assertFalse(self._in_atomic_block)