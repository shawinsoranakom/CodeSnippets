def reduction(self, dtype, src_dtype, reduction_type, value):
        """
        Perform vectorized reduction operation.

        This method handles vectorized reduction for different reduction types.
        It manages special cases for low-precision floating point types and
        employs precision improvement techniques for certain reduction operations.

        Args:
            dtype: The output data type for the reduction result
            src_dtype: The source data type of the input value
            reduction_type: Type of reduction operation (sum, min, max, etc.)
            value: The input value to reduce

        Returns:
            The result of the reduction operation
        """
        # Note: For argmax and argmin on bool type, we always convert bool to float.
        # Fix issue: https://github.com/pytorch/pytorch/issues/143568
        assert reduction_type in VECTORIZABLE_RTYPES
        argmax_or_argmin = reduction_type in ("argmax", "argmin")
        horizontal_reduction = self.tiling_idx >= self.reduction_depth
        init_dtype = src_dtype if argmax_or_argmin else dtype
        assert isinstance(value, CppCSEVariable), value

        if not value.is_vec:
            value = self.broadcast(value)

        reduction_key = src_dtype, reduction_type, value
        if reduction_key in self.reduction_cse.reduction_cache:
            return self.reduction_cse.reduction_cache[reduction_key]

        vec_ns = "at::vec"
        vec = f"{vec_ns}::Vectorized<{DTYPE_TO_CPP[dtype]}>"
        acc_type = reduction_acc_type(reduction_type, init_dtype)
        acc_type_vec = self.reduction_acc_type_vec(reduction_type, init_dtype)

        acc = self.reduction_cse.generate(
            self.loads, f"reduction {reduction_key}", write=False
        )
        assert isinstance(acc, CppCSEVariable)
        acc_vec = f"{acc}_vec"
        masked_acc = f"masked_{acc}"
        masked_acc_vec = f"masked_{acc_vec}"
        self.reduction_var_names += [f"{acc}", acc_vec, masked_acc_vec]
        self.is_reduction = True
        self.reduction_prefix_generators.append(
            self._gen_reduction_prefix(
                acc, acc_type, reduction_type, init_dtype, reduction_init
            )
        )
        self.reduction_prefix_generators.append(
            self._gen_reduction_prefix(
                acc_vec,
                acc_type_vec,
                reduction_type,
                init_dtype,
                self.reduction_init_vec,
            )
        )

        use_acc_helper = self.need_use_acc_helper(reduction_type, dtype, False)
        if use_acc_helper:
            # use masked acc_vec for tail vec kernel
            self.reduction_prefix_generators.append(
                self._gen_reduction_prefix(
                    masked_acc_vec,
                    acc_type_vec,
                    reduction_type,
                    dtype,
                    self.reduction_init_vec,
                )
            )

            # use welford_helper/cascade_helper for vec kernel
            assert self.reduction_depth is not None
            reduction_size = functools.reduce(
                operator.mul, self.ranges[self.reduction_depth :]
            )
            if reduction_type == "welford_reduce":
                helper_val = self.welford_helper_cse.generate(
                    self.compute, f"reduction {reduction_key}", write=False
                )
            else:
                helper_val = self.cascade_helper_cse.generate(
                    self.compute, f"reduction {reduction_key}", write=False
                )
            masked_helper_val = f"masked_{helper_val}"
            helper_vec_range = (
                (
                    FloorDiv(reduction_size, self.ranges[self.tiling_idx])
                    * FloorDiv(self.ranges[self.tiling_idx], self.tiling_factor)
                    if self.tiling_idx >= self.reduction_depth
                    else reduction_size
                )
                if FloorDiv(self.ranges[self.tiling_idx], self.tiling_factor)
                else sympy.Integer(0)
            )
            masked_helper_vec_range = (
                (
                    FloorDiv(reduction_size, self.ranges[self.tiling_idx])
                    if self.tiling_idx >= self.reduction_depth
                    else reduction_size
                )
                if self.ranges[self.tiling_idx] % self.tiling_factor
                else sympy.Integer(0)
            )
            # scalar helper for scalar welford_reduce/sum is also needed when vec kernel is included
            scalar_helper_val = f"scalar_{helper_val}"
            self._use_acc_helper(
                reduction_type,
                acc,
                scalar_helper_val,
                reduction_size,
                dtype,
                use_scalar=True,
            )
            self._use_acc_helper(
                reduction_type, acc, helper_val, helper_vec_range, dtype
            )
            self._use_acc_helper(
                reduction_type,
                masked_acc,
                masked_helper_val,
                masked_helper_vec_range,
                dtype,
            )

            # use masked acc_vec for tail vec kernel
            acc_vec_ = masked_acc_vec if self.tail_size else acc_vec
            helper_val_ = masked_helper_val if self.tail_size else helper_val
            if reduction_type == "sum":
                self.stores.writeline(
                    f"{acc_vec_} = {self.reduction_combine_vec(reduction_type, acc_vec_, value, helper_val_)};"
                )
            else:
                self.stores.writeline(
                    f"{acc_vec_} = {self.reduction_combine_vec(reduction_type, acc_vec_, value, helper_val_)};"
                )
        else:
            assert self.reduction_depth is not None
            index = self.itervars[self.reduction_depth]
            for i in range(self.reduction_depth + 1, len(self.itervars)):
                index = index * self.ranges[i] + self.itervars[i]
            kwargs = {
                "next_value": value,
                "index": index,
                "horizontal_reduction": horizontal_reduction,
                "src_dtype": src_dtype,
            }
            self.stores.writeline(
                f"{acc_vec} = {self.reduction_combine_vec(reduction_type, acc_vec, **kwargs)};"
            )
        self._gen_parallel_reduction_buffers(
            acc_vec,
            acc_type_vec,
            reduction_type,
            init_dtype,
            reduction_combine_fn=self.reduction_combine_vec,
            reduction_init_fn=self.reduction_init_vec,
        )
        self._gen_parallel_reduction_buffers(
            acc,
            acc_type,
            reduction_type,
            init_dtype,
            reduction_combine_fn=reduction_combine,
            reduction_init_fn=reduction_init,
        )
        if use_acc_helper:
            # use masked acc_vec for tail vec kernel
            self._gen_parallel_reduction_buffers(
                masked_acc_vec,
                acc_type_vec,
                reduction_type,
                dtype,
                reduction_combine_fn=self.reduction_combine_vec,
                reduction_init_fn=self.reduction_init_vec,
            )
        tmpvar: str | CSEVariable
        is_bool = dtype == torch.bool
        if horizontal_reduction:
            # Horizontal reduction
            if is_welford_reduction(reduction_type):
                assert self._get_num_vectors(dtype) in [
                    1,
                    2,
                ], "Welford reduction does not support VectorizedN (N>2)"
                next_value = f"welford_vec_reduce_all({acc_vec})"
                masked_next_value = f"welford_vec_reduce_all({masked_acc_vec})"
                self.reduction_suffix.writeline(
                    f"{acc} = {reduction_combine(reduction_type, acc, masked_next_value)};"
                )
            elif argmax_or_argmin:
                next_value = f"{reduction_type}_vec_reduce_all({acc_vec})"
            elif is_bool:
                if reduction_type in (
                    "any",
                    "sum",
                    "max",
                ):
                    next_value = f"!{acc_vec}.all_zero()"
                else:
                    assert reduction_type == "min"
                    next_value = f"{acc_vec}.all_masked()"
            else:
                reduce_all_body = (
                    "{ return "
                    + self.reduction_combine_vec(reduction_type, "x", "y")
                    + "; }"
                )
                is_bool = dtype == torch.bool
                # we are using at::vec::VecMask<float, N> for bool
                vec_dtype = torch.float if is_bool else dtype
                vec = f"at::vec::Vectorized<{DTYPE_TO_CPP[vec_dtype]}>"
                vec_reduce_all_func = f"at::vec::vec_reduce_all<{DTYPE_TO_CPP[vec_dtype]}, {self._get_num_vectors(vec_dtype)}>"
                result_vec = f"{acc_vec}"
                if use_acc_helper:
                    assert reduction_type == "sum"
                    result_vec = f"{acc_vec} + {masked_acc_vec}"
                next_value = f"{vec_reduce_all_func}([]({vec}& x, {vec}& y) {reduce_all_body}, {result_vec})"

            self.reduction_suffix.writeline(
                f"{acc} = {reduction_combine(reduction_type, acc, next_value, src_dtype=src_dtype)};"
            )
            tmpvar = acc
        else:
            tmpvar = acc_vec
            if is_welford_reduction(reduction_type):
                masked_tmpvar = f"masked_{tmpvar}"
                self.reduction_suffix.writeline(
                    f"{tmpvar} = {reduction_combine(reduction_type, tmpvar, masked_tmpvar)};"
                )
            elif use_acc_helper:
                assert reduction_type == "sum"
                masked_tmpvar = f"masked_{tmpvar}"
                self.reduction_suffix.writeline(
                    f"{tmpvar} = {tmpvar} + {masked_tmpvar};"
                )

        result = reduction_project(reduction_type, tmpvar)
        self.reduction_cse.reduction_cache[reduction_key] = result
        return result