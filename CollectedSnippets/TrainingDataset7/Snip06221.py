def params(self):
        argon2 = self._load_library()
        # salt_len is a noop, because we provide our own salt.
        return argon2.Parameters(
            type=argon2.low_level.Type.ID,
            version=argon2.low_level.ARGON2_VERSION,
            salt_len=argon2.DEFAULT_RANDOM_SALT_LENGTH,
            hash_len=argon2.DEFAULT_HASH_LENGTH,
            time_cost=self.time_cost,
            memory_cost=self.memory_cost,
            parallelism=self.parallelism,
        )