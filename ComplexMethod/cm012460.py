def aggregate_reduction_prefix_suffix(outer_loop: "LoopLevel"):
            assert len(self.kernels) >= 2
            main_loop_kernel = self.kernels[0]
            tail_loop_kernel = self.kernels[-1]
            assert isinstance(main_loop_kernel, self.vec_kernel_cls)

            # Prefix
            if type(tail_loop_kernel) is self.kernel_cls:
                # if tail loop kernel is a scalar kernel, we need to extend tmp_acc -> tmp_acc_arr[] to
                # hold the temporary inner loop acc result for outer tail loop
                tail_loop_kernel.finalize_reduction_prefix(
                    main_loop_kernel.tiling_factor
                )
                main_loop_kernel.finalize_reduction_prefix()
                self.reduction_prefix.splice(
                    tail_loop_kernel.reduction_prefix
                    + main_loop_kernel.reduction_prefix
                )
            else:
                main_loop_kernel.finalize_reduction_prefix()
                self.reduction_prefix.splice(main_loop_kernel.reduction_prefix)

            # Suffix
            suffix_buf = BracesBuffer()
            with contextlib.ExitStack() as stack:
                if main_loop_kernel.codegen_conditions(
                    suffix_buf, "C10_LIKELY", outer_loop.var
                ):
                    stack.enter_context(suffix_buf.indent())
                    suffix_buf.splice(main_loop_kernel.reduction_suffix)
            with contextlib.ExitStack() as stack:
                if tail_loop_kernel.codegen_conditions(
                    suffix_buf, "C10_UNLIKELY", outer_loop.var
                ):
                    stack.enter_context(suffix_buf.indent())
                    if type(tail_loop_kernel) is self.kernel_cls:
                        reduction_vars = tail_loop_kernel.reduction_var_names
                        for name in reduction_vars:
                            new_name = f"{name}_arr[{outer_loop.var}_tail - {cexpr_index(outer_loop.tiled_size)}]"
                            replace_acc_name(tail_loop_kernel.stores, name, new_name)
                            replace_acc_name(
                                tail_loop_kernel.reduction_suffix, name, new_name
                            )
                        # If tail loop kernel is a scalar kernel, use direct sum instead of cascade_sum_combine
                        # as the reduction vars are extended: tmp_acc -> tmp_acc_arr[].
                        replace_cascade_sum_with_add(tail_loop_kernel.stores)
                        suffix_buf.splice(
                            move_code_under_inner_loop(
                                tail_loop_kernel.reduction_suffix,
                                outer_loop.var,
                                f"{outer_loop.var}_tail",
                                outer_loop.tiled_size,
                                outer_loop.size,
                            )
                        )
                    else:
                        suffix_buf.splice(tail_loop_kernel.reduction_suffix)
            self.reduction_suffix = suffix_buf