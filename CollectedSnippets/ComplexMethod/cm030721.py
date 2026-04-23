def _check_notify(self, cond):
        # Note that this test is sensitive to timing.  If the worker threads
        # don't execute in a timely fashion, the main thread may think they
        # are further along then they are.  The main thread therefore issues
        # wait_threads_blocked() statements to try to make sure that it doesn't
        # race ahead of the workers.
        # Secondly, this test assumes that condition variables are not subject
        # to spurious wakeups.  The absence of spurious wakeups is an implementation
        # detail of Condition Variables in current CPython, but in general, not
        # a guaranteed property of condition variables as a programming
        # construct.  In particular, it is possible that this can no longer
        # be conveniently guaranteed should their implementation ever change.
        ready = []
        results1 = []
        results2 = []
        phase_num = 0
        def f():
            cond.acquire()
            ready.append(phase_num)
            result = cond.wait()

            cond.release()
            results1.append((result, phase_num))

            cond.acquire()
            ready.append(phase_num)

            result = cond.wait()
            cond.release()
            results2.append((result, phase_num))

        N = 5
        with Bunch(f, N):
            # first wait, to ensure all workers settle into cond.wait() before
            # we continue. See issues #8799 and #30727.
            for _ in support.sleeping_retry(support.SHORT_TIMEOUT):
                if len(ready) >= N:
                    break

            ready.clear()
            self.assertEqual(results1, [])

            # Notify 3 threads at first
            count1 = 3
            cond.acquire()
            cond.notify(count1)
            wait_threads_blocked(count1)

            # Phase 1
            phase_num = 1
            cond.release()
            for _ in support.sleeping_retry(support.SHORT_TIMEOUT):
                if len(results1) >= count1:
                    break

            self.assertEqual(results1, [(True, 1)] * count1)
            self.assertEqual(results2, [])

            # Wait until awaken workers are blocked on cond.wait()
            for _ in support.sleeping_retry(support.SHORT_TIMEOUT):
                if len(ready) >= count1 :
                    break

            # Notify 5 threads: they might be in their first or second wait
            cond.acquire()
            cond.notify(5)
            wait_threads_blocked(N)

            # Phase 2
            phase_num = 2
            cond.release()
            for _ in support.sleeping_retry(support.SHORT_TIMEOUT):
                if len(results1) + len(results2) >= (N + count1):
                    break

            count2 = N - count1
            self.assertEqual(results1, [(True, 1)] * count1 + [(True, 2)] * count2)
            self.assertEqual(results2, [(True, 2)] * count1)

            # Make sure all workers settle into cond.wait()
            for _ in support.sleeping_retry(support.SHORT_TIMEOUT):
                if len(ready) >= N:
                    break

            # Notify all threads: they are all in their second wait
            cond.acquire()
            cond.notify_all()
            wait_threads_blocked(N)

            # Phase 3
            phase_num = 3
            cond.release()
            for _ in support.sleeping_retry(support.SHORT_TIMEOUT):
                if len(results2) >= N:
                    break
            self.assertEqual(results1, [(True, 1)] * count1 + [(True, 2)] * count2)
            self.assertEqual(results2, [(True, 2)] * count1 + [(True, 3)] * count2)