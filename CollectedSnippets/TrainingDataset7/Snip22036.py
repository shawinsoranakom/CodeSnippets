def test_shared_lock(self):
        file_path = Path(__file__).parent / "test.png"
        with open(file_path) as f1, open(file_path) as f2:
            self.assertIs(locks.lock(f1, locks.LOCK_SH), True)
            self.assertIs(locks.lock(f2, locks.LOCK_SH | locks.LOCK_NB), True)
            self.assertIs(locks.unlock(f1), True)
            self.assertIs(locks.unlock(f2), True)