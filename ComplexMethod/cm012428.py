def decide_parallel_depth(self, max_parallel_depth, threads):
        assert self.call_ranges is not None
        ranges = self.call_ranges[
            max_parallel_depth.start_depth : (
                max_parallel_depth.start_depth + max_parallel_depth.parallel_depth
            )
        ]
        seq = self.size_hint()
        par = 1
        depth = 0
        for expr in ranges:
            hint = V.graph.sizevars.optimization_hint(expr, fallback=8192)
            if par >= 2 * threads or par == threads:
                break
            if seq // threads < config.cpp.min_chunk_size:
                # not enough work
                break
            depth += 1
            par *= hint
            seq /= hint
        # if we assume thread number is dynamic, make sure we
        # have at least one parallel scope and let OMP runtime
        # to manage the serial vs. parallel.
        if config.cpp.dynamic_threads and depth == 0 and len(ranges) > 0:
            depth = 1
        return ParallelDepth(
            parallel_depth=depth, start_depth=max_parallel_depth.start_depth
        )