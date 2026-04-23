def test_acquire_with_timeout(
        self,
        lock_typename: str,
        lock_timeout: str,
        acquisition_mode: str,
        release: str,
    ) -> None:
        """Test lock acquisition behavior with various timeout configurations and release scenarios.

        This comprehensive test verifies the lock acquisition functionality for both threading.Lock
        and FileLock objects across different timeout modes, acquisition patterns, and release timings.
        The test validates proper exception handling, timeout behavior, and correct lock state management.

        Test parameters:
        - lock_typename: Tests both "Lock" (threading.Lock) and "FileLock" (filelock.FileLock) types
        - lock_timeout: Tests "BLOCKING", "NON_BLOCKING", and "BLOCKING_WITH_TIMEOUT" modes
        - acquisition_mode: Tests both "safe" (context manager) and "unsafe" (manual) acquisition
        - release: Tests "unlocked", "never", "before_timeout", and "after_timeout" scenarios

        The test ensures that:
        - Safe acquisition properly manages lock lifecycle through context managers
        - Unsafe acquisition requires manual release and behaves correctly
        - Timeout exceptions are raised appropriately for different timeout configurations
        - Lock states are correctly maintained throughout acquisition and release cycles
        - Different lock types (Lock vs FileLock) behave consistently with their respective APIs
        """

        def inner(lock_or_flock: Lock | FileLock, timeout: int) -> None:
            if self.is_lock(lock_or_flock):
                lock: Lock = lock_or_flock
                if acquisition_mode == "safe":
                    with locks._acquire_lock_with_timeout(lock, timeout=timeout):
                        self.assertTrue(self.lock_or_flock_locked(lock))
                elif acquisition_mode == "unsafe":
                    locks._unsafe_acquire_lock_with_timeout(lock, timeout=timeout)
                    self.assertTrue(self.lock_or_flock_locked(lock))
                    lock.release()
                else:
                    raise NotImplementedError
            elif self.is_flock(lock_or_flock):
                flock: FileLock = lock_or_flock
                if acquisition_mode == "safe":
                    with locks._acquire_flock_with_timeout(flock, timeout=timeout):
                        self.assertTrue(self.lock_or_flock_locked(flock))
                elif acquisition_mode == "unsafe":
                    locks._unsafe_acquire_flock_with_timeout(flock, timeout=timeout)
                    self.assertTrue(self.lock_or_flock_locked(flock))
                    flock.release()
                else:
                    raise NotImplementedError
            else:
                raise NotImplementedError
            self.assertFalse(self.lock_or_flock_locked(lock_or_flock))

        if lock_typename not in ["Lock", "FileLock"]:
            raise AssertionError(f"Unexpected lock_typename: {lock_typename}")
        flock_fpath: Path = (
            impls._OnDiskCacheImpl()._cache_dir
            / f"testing-locks-instance-{self.random_string}.lock"
        )
        lock_or_flock: Lock | FileLock = (
            Lock() if lock_typename == "Lock" else FileLock(str(flock_fpath))
        )
        lock_exception_type: type = (
            exceptions.LockTimeoutError
            if lock_typename == "Lock"
            else exceptions.FileLockTimeoutError
        )

        if release == "unlocked":
            self.assertFalse(self.lock_or_flock_locked(lock_or_flock))
        elif release in ["never", "before_timeout", "after_timeout"]:
            self.assertTrue(lock_or_flock.acquire(timeout=locks._NON_BLOCKING))
            self.assertTrue(self.lock_or_flock_locked(lock_or_flock))
        else:
            raise NotImplementedError

        with self.executor() as executor:
            if lock_timeout not in [
                "BLOCKING",
                "NON_BLOCKING",
                "BLOCKING_WITH_TIMEOUT",
            ]:
                raise AssertionError(f"Unexpected lock_timeout: {lock_timeout}")
            lock_or_flock_future: Future[None] = executor.submit(
                inner,
                lock_or_flock,
                timeout={
                    "BLOCKING": locks._BLOCKING,
                    "NON_BLOCKING": locks._NON_BLOCKING,
                    "BLOCKING_WITH_TIMEOUT": locks._BLOCKING_WITH_TIMEOUT,
                }[lock_timeout],
            )

            if release == "unlocked":
                self.assertIsNone(lock_or_flock_future.result())
            elif release == "never":
                wait([lock_or_flock_future], timeout=(locks._BLOCKING_WITH_TIMEOUT * 2))
                if lock_timeout == "BLOCKING":
                    with self.assertRaises(TimeoutError):
                        lock_or_flock_future.result(
                            timeout=locks._BLOCKING_WITH_TIMEOUT
                        )
                elif lock_timeout in ["NON_BLOCKING", "BLOCKING_WITH_TIMEOUT"]:
                    with self.assertRaises(lock_exception_type):
                        lock_or_flock_future.result()
                else:
                    raise NotImplementedError
                lock_or_flock.release()
            elif release == "before_timeout":
                wait([lock_or_flock_future], timeout=(locks._BLOCKING_WITH_TIMEOUT / 2))
                lock_or_flock.release()
                if lock_timeout in ["BLOCKING", "BLOCKING_WITH_TIMEOUT"]:
                    self.assertIsNone(lock_or_flock_future.result())
                elif lock_timeout == "NON_BLOCKING":
                    with self.assertRaises(lock_exception_type):
                        lock_or_flock_future.result()
                else:
                    raise NotImplementedError
            elif release == "after_timeout":
                wait([lock_or_flock_future], timeout=(locks._BLOCKING_WITH_TIMEOUT * 2))
                lock_or_flock.release()
                if lock_timeout == "BLOCKING":
                    self.assertIsNone(lock_or_flock_future.result())
                elif lock_timeout in ["NON_BLOCKING", "BLOCKING_WITH_TIMEOUT"]:
                    with self.assertRaises(lock_exception_type):
                        lock_or_flock_future.result()
                else:
                    raise NotImplementedError

        flock_fpath.unlink(missing_ok=True)