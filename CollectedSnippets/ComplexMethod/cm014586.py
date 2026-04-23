def get_m_k_n(self, dtype: Any) -> tuple[int, int, int]:
        numel_max = 2**31

        # repeat until tensors fit in memory
        while True:
            m = self.get_random_num_small()
            k = self.get_random_dim()
            n = self.get_random_dim()
            if k % 256 != 0:
                continue

            if not (k >= 1024 and n >= 1024):
                raise AssertionError("k and n must be at least 1024")

            if m * k >= numel_max or m * n >= numel_max or k * n >= numel_max:
                # autotuning will not happen for tensors that are this large
                continue

            if fits_in_memory(dtype, m, k, n):
                return (m, k, n)