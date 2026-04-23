def _thread_blocking(self, num_threads: int) -> GemmBlocking:
        """
        NOTE [Thread blocking in Cpp GEMM]
        We use simple heuristics to decide the thread blocking:
        1. Make sure all threads are occupied as much as possible.
        2. For (m, n) blocks, favor more square-sized thread blocks for better data reuse.
        3. If (m, n) blocks cannot occupy all the threads, we consider k-slicing.
        TODO(jgong5): allow tuning various blocking options
        """

        def get_factors(number):
            factors = []
            for i in range(int(number**0.5), 0, -1):
                if number % i == 0:
                    factors.append(number // i)
                    factors.append(i)
            return factors

        def get_blocking(m_factor, n_factor, k_factor, m_blocks, n_blocks, k_blocks):
            thread_block_k = math.ceil(k_blocks / k_factor)
            thread_block_n = math.ceil(n_blocks / n_factor)
            thread_block_m = math.ceil(m_blocks / m_factor)
            return GemmBlocking(thread_block_m, thread_block_n, thread_block_k)

        assert not self.is_dynamic_M, (
            "Unable to determine thread blocking for dynamic M."
        )
        register_blocking = self.register_blocking
        m_blocks = math.ceil(self.m / register_blocking.block_m)
        n_blocks = math.ceil(self.n / register_blocking.block_n)
        k_blocks = math.ceil(self.k / register_blocking.block_k)
        factors = get_factors(num_threads)
        assert len(factors) > 0

        if config.cpp.gemm_thread_factors is not None:
            factors = [int(i) for i in config.cpp.gemm_thread_factors.split(",")]
            assert len(factors) == 3
            assert math.prod(factors) == self.num_threads
            return get_blocking(
                factors[0], factors[1], factors[2], m_blocks, n_blocks, k_blocks
            )

        # we favor square-sized thread blocks for good data reuse
        def get_better_blocking(blocking, best_blocking):
            if best_blocking is None:
                best_blocking = blocking
            else:
                block_m_size = blocking.block_m * register_blocking.block_m
                block_n_size = blocking.block_n * register_blocking.block_n
                best_block_m_size = best_blocking.block_m * register_blocking.block_m
                best_block_n_size = best_blocking.block_n * register_blocking.block_n
                if blocking.block_k > best_blocking.block_k:
                    best_blocking = blocking
                elif (
                    blocking.block_k == best_blocking.block_k
                    and block_m_size + block_n_size
                    < best_block_m_size + best_block_n_size
                ):
                    best_blocking = blocking
            return best_blocking

        best_blocking = None
        # check if we can have a thread-blocking to occupy all threads without k-slicing
        for n_factor in factors:
            m_factor = num_threads // n_factor
            if n_blocks >= n_factor and m_blocks >= m_factor:
                blocking = get_blocking(
                    m_factor, n_factor, 1, m_blocks, n_blocks, k_blocks
                )
                best_blocking = get_better_blocking(blocking, best_blocking)

        if best_blocking is None:
            for k_factor in factors:
                if k_blocks >= k_factor and (
                    config.cpp.gemm_max_k_slices == 0
                    or k_factor <= config.cpp.gemm_max_k_slices
                ):
                    n_factors = get_factors(num_threads // k_factor)
                    for n_factor in n_factors:
                        m_factor = (num_threads // k_factor) // n_factor
                        if n_blocks >= n_factor and m_blocks >= m_factor:
                            blocking = get_blocking(
                                m_factor,
                                n_factor,
                                k_factor,
                                m_blocks,
                                n_blocks,
                                k_blocks,
                            )
                            best_blocking = get_better_blocking(blocking, best_blocking)

        if best_blocking is None:
            for n_factor in factors:
                m_factor = num_threads // n_factor
                if n_blocks >= n_factor or m_blocks >= m_factor:
                    blocking = get_blocking(
                        m_factor, n_factor, 1, m_blocks, n_blocks, k_blocks
                    )
                    best_blocking = get_better_blocking(blocking, best_blocking)

        assert best_blocking is not None
        return best_blocking