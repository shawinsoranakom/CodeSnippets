def notify(self, n=1):
        assert self._lock._semlock._is_mine(), 'lock is not owned'
        assert not self._wait_semaphore.acquire(
            False), ('notify: Should not have been able to acquire '
                     + '_wait_semaphore')

        # to take account of timeouts since last notify*() we subtract
        # woken_count from sleeping_count and rezero woken_count
        while self._woken_count.acquire(False):
            res = self._sleeping_count.acquire(False)
            assert res, ('notify: Bug in sleeping_count.acquire'
                         + '- res should not be False')

        sleepers = 0
        while sleepers < n and self._sleeping_count.acquire(False):
            self._wait_semaphore.release()        # wake up one sleeper
            sleepers += 1

        if sleepers:
            for i in range(sleepers):
                self._woken_count.acquire()       # wait for a sleeper to wake

            # rezero wait_semaphore in case some timeouts just happened
            while self._wait_semaphore.acquire(False):
                pass