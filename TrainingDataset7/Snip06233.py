def must_update(self, encoded):
        decoded = self.decode(encoded)
        return (
            decoded["work_factor"] != self.work_factor
            or decoded["block_size"] != self.block_size
            or decoded["parallelism"] != self.parallelism
        )