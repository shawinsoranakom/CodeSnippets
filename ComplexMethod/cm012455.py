def max_parallel_depth(self):
        """
        Maximal allowed depth for parallelism: All reduction or non-reduction levels.
        When the range of the first inner loop beyond the maximum parallel depth is much
        larger than the range of all outer loops within the maximum parallel depth,
        change the starting depth of parallelism to the first inner loop and recalculate
        the maximum parallel depth.
        """
        if self.loops is None:
            return ParallelDepth(parallel_depth=0, start_depth=0)

        start_depth = 0
        max_depth = 0
        is_reduction = self.loops[0].is_reduction
        num_steps = sympy.Integer(1)
        for loop in self.loops:
            if loop.is_reduction != is_reduction:
                break
            num_steps = num_steps * FloorDiv(loop.size, loop.steps)
            max_depth += 1

        def get_simd_vec_depth(loops):
            # Return the first loop level which is simd_vec
            for i, loop in enumerate(loops):
                if loop.simd_vec:
                    return i
            return None

        simd_vec_depth = get_simd_vec_depth(self.loops)

        def has_scalar_kernel(loop_nest: LoopNest):
            assert isinstance(loop_nest.kernel, CppKernelProxy)
            return any(
                not isinstance(kernel, CppVecKernel)
                for kernel in loop_nest.kernel.kernels
            )

        # When the number of steps of the first inner loop is much larger than the number of steps of
        # all outer loops, change `start_depth` to the first inner loop and recalculate `max_depth`.
        if (
            max_depth < len(self.loops)
            and isinstance(num_steps, sympy.Integer)
            and isinstance(self.loops[max_depth].size, sympy.Integer)
            and num_steps * 300
            < FloorDiv(self.loops[max_depth].size, self.loops[max_depth].steps)
            and not (
                # Disable parallel reduction under the vec loop
                simd_vec_depth is not None
                and max_depth > simd_vec_depth
                and self.loops[max_depth].is_reduction
                and has_scalar_kernel(self)
            )
        ):
            start_depth = max_depth
            max_depth = 0
            is_reduction = self.loops[start_depth].is_reduction
            for i in range(start_depth, len(self.loops)):
                if self.loops[i].is_reduction != is_reduction:
                    break
                max_depth += 1
        return ParallelDepth(parallel_depth=max_depth, start_depth=start_depth)