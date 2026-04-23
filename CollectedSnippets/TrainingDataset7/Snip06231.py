def verify(self, password, encoded):
        decoded = self.decode(encoded)
        encoded_2 = self.encode(
            password,
            decoded["salt"],
            decoded["work_factor"],
            decoded["block_size"],
            decoded["parallelism"],
        )
        return constant_time_compare(encoded, encoded_2)