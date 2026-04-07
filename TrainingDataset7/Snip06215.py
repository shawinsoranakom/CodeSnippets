def encode(self, password, salt):
        argon2 = self._load_library()
        params = self.params()
        data = argon2.low_level.hash_secret(
            force_bytes(password),
            force_bytes(salt),
            time_cost=params.time_cost,
            memory_cost=params.memory_cost,
            parallelism=params.parallelism,
            hash_len=params.hash_len,
            type=params.type,
        )
        return self.algorithm + data.decode("ascii")