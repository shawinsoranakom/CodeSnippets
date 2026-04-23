def _handle_higher_order_ops(self, func, types, args, kwargs):
        is_triton = func in {torch.ops.higher_order.triton_kernel_wrapper_mutation,
                             torch.ops.higher_order.triton_kernel_wrapper_functional}
        if is_triton:
            from torch._higher_order_ops.triton_kernel_wrap import get_kernel
            # Special case - look in the triton flop registry for the kernel
            from triton.runtime.jit import JITFunction
            kernel_name = get_kernel(kwargs["kernel_idx"])
            # Unwrap heuristics if they are present
            while not isinstance(kernel_name, JITFunction):
                if hasattr(kernel_name, "fn"):
                    kernel_name = kernel_name.fn
                else:
                    break
            return self.counter._count_flops(kernel_name, None, args, kwargs)
        elif func is torch.ops.higher_order.cond:
            # The flop counter for cond counts the upper bound of flops.
            # For example, if a matmul is executed 2 times in true branch
            # but only 1 time in the false branch, the flop counter will
            # record the larger number of flops, i.e. 2 times.
            pred, true_branch, false_branch, operands = args
            # Step 1: Count flops for true branch and false branch separately
            true_out, true_flop_counts = self._execute_with_isolated_flop_counting(
                true_branch, operands
            )
            if true_out is NotImplemented:
                return NotImplemented

            false_out, false_flop_counts = self._execute_with_isolated_flop_counting(
                false_branch, operands
            )
            if false_out is NotImplemented:
                return NotImplemented

            # Step 2: merge flop counts
            all_mod_keys = set(true_flop_counts.keys()) | set(false_flop_counts.keys())
            merged_flop_counts = {}
            for outer_key in all_mod_keys:
                true_func_counts = true_flop_counts[outer_key]
                false_func_counts = false_flop_counts[outer_key]

                merged_func_counts = {}
                all_func_keys = set(true_func_counts.keys()) | set(false_func_counts.keys())

                for func_key in all_func_keys:
                    true_val = true_func_counts.get(func_key, 0)
                    false_val = false_func_counts.get(func_key, 0)
                    merged_func_counts[func_key] = max(true_val, false_val)

                merged_flop_counts[outer_key] = merged_func_counts

            # Step 3: update the counter with merged counts
            for outer_key, inner_dict in merged_flop_counts.items():
                self.counter.flop_counts[outer_key].update(inner_dict)

            # It doesn't matter which one we return since true_fn and false_fn return
            # output with the same structure.
            return true_out
        else:
            return NotImplemented