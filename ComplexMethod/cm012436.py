def reduction_combine_vec(
        self,
        reduction_type,
        var,
        next_value,
        helper_val=None,
        index: sympy.Symbol | None = None,
        horizontal_reduction: bool | None = None,
        src_dtype: torch.dtype | None = torch.float32,
    ):
        is_bool = src_dtype == torch.bool
        if reduction_type == "max":
            if self.tail_size:
                return f"max_masked_reduce({var}, {next_value}, {cexpr_index(self.tail_size)})"
            else:
                return (
                    f"{var} | {next_value}"
                    if is_bool
                    else f"at::vec::maximum({var}, {next_value})"
                )
        elif reduction_type == "min":
            if self.tail_size:
                return f"min_masked_reduce({var}, {next_value}, {cexpr_index(self.tail_size)})"
            else:
                return (
                    f"{var} & {next_value}"
                    if is_bool
                    else f"at::vec::minimum({var}, {next_value})"
                )
        elif reduction_type == "sum":
            if helper_val:
                if self.tail_size:
                    return f"cascade_sum_combine({next_value}, {cexpr_index(self.tail_size)}, &{helper_val})"
                else:
                    return f"cascade_sum_combine({next_value}, &{helper_val})"
            else:
                if self.tail_size:
                    return f"sum_masked_reduce({var}, {next_value}, {cexpr_index(self.tail_size)})"
                else:
                    conjunction = "|" if is_bool else "+"
                    return f"{var} {conjunction} {next_value}"
        elif reduction_type == "prod":
            if self.tail_size:
                return f"prod_masked_reduce({var}, {next_value}, {cexpr_index(self.tail_size)})"
            else:
                return f"{var} * {next_value}"
        elif reduction_type == "xor_sum":
            if self.tail_size:
                return f"xor_sum_masked_reduce({var}, {next_value}, {cexpr_index(self.tail_size)})"
            else:
                return f"{var} ^ {next_value}"
        elif reduction_type == "welford_reduce":
            if helper_val:
                if self.tail_size:
                    return f"welford_combine({var}, {next_value}, {cexpr_index(self.tail_size)}, &{helper_val})"
                else:
                    return f"welford_combine({var}, {next_value}, &{helper_val})"
            else:
                if self.tail_size:
                    return f"welford_combine({var}, {next_value}, {cexpr_index(self.tail_size)})"
                else:
                    return f"welford_combine({var}, {next_value})"
        elif reduction_type == "welford_combine":
            if isinstance(next_value, tuple):
                # When reading a value from Inductor IR we have a tuple of variable names
                mean, m2, weight = next_value
            else:
                # When combining intermediate accumulators we have a Welford<T> struct
                mean, m2, weight = reduction_project(reduction_type, next_value)
            if self.tail_size:
                return f"welford_combine({var}, {{{mean}, {m2}, {weight}}}, {cexpr_index(self.tail_size)})"
            else:
                return f"welford_combine({var}, {{{mean}, {m2}, {weight}}})"
        elif reduction_type in ("argmin", "argmax"):
            assert src_dtype is not None
            cdtype = DTYPE_TO_CPP[src_dtype]
            compute_dtype = src_dtype
            if src_dtype == torch.bool:
                # For bool argmin/argmax, we use float for computations
                cdtype = DTYPE_TO_CPP[torch.float]
                compute_dtype = torch.float
                # Convert bool VecMask to float vector for argmax_combine_vec
                if isinstance(next_value, CppCSEVariable) and next_value.is_vec:
                    (next_value,) = unify_mask_base_type(self.compute, (next_value,))
            n_src = self._get_num_vectors(compute_dtype)
            n_idx = self._get_num_vectors(torch.int64)
            t_extra = ""
            arg_extra = ""
            if index is not None:
                assert horizontal_reduction is not None
                t_extra = f", {str(horizontal_reduction).lower()}"
                arg_extra = f", {self._adjust_argreduce_index(index)}"
            if self.tail_size:
                return (
                    f"{reduction_type}_combine_vec<{cdtype}, {n_src}, {n_idx}{t_extra}>"
                    f"({var}, {next_value}{arg_extra}, {cexpr_index(self.tail_size)})"
                )
            else:
                return f"{reduction_type}_combine_vec<{cdtype}, {n_src}, {n_idx}{t_extra}>({var}, {next_value}{arg_extra})"
        elif reduction_type == "any":
            if isinstance(next_value, CppCSEVariable):
                assert next_value.dtype == torch.bool
                (next_value,) = unify_mask_base_type(V.kernel.compute, (next_value,))
            if self.tail_size:
                return f"any_masked_reduce({var}, {next_value}, {cexpr_index(self.tail_size)})"
            else:
                return f"{var} | {next_value}"
        else:
            raise NotImplementedError