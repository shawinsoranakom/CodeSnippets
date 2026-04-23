def test_argon2_upgrade(self):
        self._test_argon2_upgrade("time_cost", "time cost", 1)
        self._test_argon2_upgrade("memory_cost", "memory cost", 64)
        self._test_argon2_upgrade("parallelism", "parallelism", 1)