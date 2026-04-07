def decode(self, encoded):
        argon2 = self._load_library()
        algorithm, rest = encoded.split("$", 1)
        assert algorithm == self.algorithm
        params = argon2.extract_parameters("$" + rest)
        variety, *_, b64salt, hash = rest.split("$")
        # Add padding.
        b64salt += "=" * (-len(b64salt) % 4)
        salt = base64.b64decode(b64salt).decode("latin1")
        return {
            "algorithm": algorithm,
            "hash": hash,
            "memory_cost": params.memory_cost,
            "parallelism": params.parallelism,
            "salt": salt,
            "time_cost": params.time_cost,
            "variety": variety,
            "version": params.version,
            "params": params,
        }