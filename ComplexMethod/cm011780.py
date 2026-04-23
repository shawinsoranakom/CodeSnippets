def reduction_split_factor(
        device: torch.device,
        reduction_numel_hint: int,
        numel_hint: int,
        inner_reduction: bool,
    ) -> int:
        """Heuristic to decide the RSPLIT used for split reductions.
        When a reduction has a small number of outputs there is not enough parallelism,
        so we will do the reduction in two phases."""
        props = DeviceProperties.create(device)
        num_sm = props.multi_processor_count
        warp_size = props.warp_size if props.warp_size is not None else 32
        max_threads_per_sm = (
            props.max_threads_per_multi_processor
            if props.max_threads_per_multi_processor is not None
            else 2048
        )
        min_elements_per_thread = warp_size
        max_elements_per_thread = 512
        threads_per_sm = max_threads_per_sm
        min_elements_per_device = min_elements_per_thread * num_sm * threads_per_sm
        max_elements_per_device = max_elements_per_thread * num_sm * threads_per_sm
        num_warps = 8
        num_threads = warp_size * num_warps

        if inner_reduction:
            # do heuristics that's close to eager mode for split inner reduction
            # we leak reduction autotune configs here, and will need to refactor to avoid this later
            if numel_hint >= 2 * num_sm:  # don't split if there are enough outputs
                return 1
            # based on sum(x[N]) on GB200, split reduction provides higher performance when N >= 1M
            # TODO: test more hardwares
            no_split_threshold = (
                524288 if props.major is not None and props.major >= 10 else 8192
            )
            if reduction_numel_hint <= no_split_threshold:
                return 1
            if reduction_numel_hint * numel_hint <= min_elements_per_device:
                split_size = min_elements_per_thread
            elif reduction_numel_hint * numel_hint < max_elements_per_device:
                target_blocks = num_sm * threads_per_sm // (2 * num_threads)
                blocks_per_output = (target_blocks + numel_hint - 1) // numel_hint
                tmp_split_size = (
                    reduction_numel_hint + num_threads * blocks_per_output - 1
                ) // (num_threads * blocks_per_output)
                divisors = sympy.divisors(reduction_numel_hint)
                closest = min(divisors, key=lambda x: abs(x - tmp_split_size))
                if abs(closest - tmp_split_size) < 30:
                    # prefer even splits, but never smalle than min_elements_per_thread
                    split_size = max(closest, min_elements_per_thread)
                else:
                    split_size = tmp_split_size
            else:
                divisors = sympy.divisors(reduction_numel_hint)
                closest = min(divisors, key=lambda x: abs(x - max_elements_per_thread))
                if abs(closest - max_elements_per_thread) < 50:
                    # prefer even splits
                    split_size = closest
                else:
                    split_size = max_elements_per_thread
            return (reduction_numel_hint + split_size * num_threads - 1) // (
                split_size * num_threads
            )
        else:
            # TODO the best heuristic currently has XBLOCK (corresponding to numel_hint) 128
            # extend to even smaller number of outputs
            rvals_per_thread = 4  # comes from heuristics, refactor to not leak here
            xvals_per_block = 128
            xblocks = (numel_hint + xvals_per_block - 1) // xvals_per_block
            if reduction_numel_hint * numel_hint < min_elements_per_device:
                split_size = min_elements_per_thread
            elif reduction_numel_hint * numel_hint < max_elements_per_device:
                target_blocks = num_sm * threads_per_sm // (num_threads)
                target_blocks = (target_blocks + xblocks - 1) // xblocks
                tmp_split_size = (
                    reduction_numel_hint + rvals_per_thread * target_blocks - 1
                ) // (rvals_per_thread * target_blocks)
                divisors = sympy.divisors(reduction_numel_hint)
                closest = min(divisors, key=lambda x: abs(x - tmp_split_size))
                if abs(tmp_split_size - closest) < 20:
                    split_size = max(closest, min_elements_per_thread)
                else:
                    split_size = tmp_split_size
            else:
                divisors = sympy.divisors(reduction_numel_hint)
                closest = min(divisors, key=lambda x: abs(x - max_elements_per_thread))
                if abs(closest - max_elements_per_thread) < 50:
                    # prefer even splits
                    split_size = closest
                else:
                    split_size = max_elements_per_thread

            return (reduction_numel_hint + rvals_per_thread * split_size - 1) // (
                rvals_per_thread * split_size
            )