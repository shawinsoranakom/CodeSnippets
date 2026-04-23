def decode(self, encoded):
        algorithm, work_factor, salt, block_size, parallelism, hash_ = encoded.split(
            "$", 6
        )
        assert algorithm == self.algorithm
        return {
            "algorithm": algorithm,
            "work_factor": int(work_factor),
            "salt": salt,
            "block_size": int(block_size),
            "parallelism": int(parallelism),
            "hash": hash_,
        }