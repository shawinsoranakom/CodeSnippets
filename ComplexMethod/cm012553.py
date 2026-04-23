def reduction(
        self,
        dtype: torch.dtype,
        src_dtype: torch.dtype,
        reduction_type: ReductionType,
        value: CSEVariable | tuple[CSEVariable, ...],
    ) -> CSEVariable | tuple[CSEVariable, ...]:
        """Codegen a reduction operation"""
        assert self.inside_reduction
        assert not self._load_mask
        cache_key = (src_dtype, reduction_type, value)
        if cache_key in self.cse.reduction_cache:
            return self.cse.reduction_cache[cache_key]

        if isinstance(value, tuple):
            assert reduction_type == "welford_combine"
            self.cse.reduction_cache[cache_key] = result_tuple = (
                self.welford_combine_impl(*value)
            )
            return result_tuple

        assert isinstance(value, HalideCSEVariable) and value.used_dims is not None
        reduction_vars = OrderedSet(self.reduction_renames)
        result_var = self.newfunc(
            [v for v in value.used_dims if v not in reduction_vars],
        )
        if reduction_vars - OrderedSet(value.used_dims):
            value = self.genfunc(
                f"{value}",
                self.sort_used_dims(OrderedSet((*value.used_dims, *reduction_vars))),
                shape=value.shape,
            )
        value_str = value.subs_str(self.reduction_renames)
        default = ir.Reduction.default_accumulator(reduction_type, src_dtype)
        acc_type = halide_acc_type(dtype)

        if reduction_type in ("argmax", "argmin"):
            index = f"{result_var.name}_{reduction_type}"
            self.body.writeline(f"{index} = hl.{reduction_type}(rdom, {value_str})")
            # turn the N-D argmax index into a 1-D one
            parts = []
            stride = 1
            for i, sym in enumerate(self.reduction_renames):
                # pyrefly: ignore [bad-argument-type]
                parts.append(f"{index}[{i}]")
                if stride != 1:
                    # pyrefly: ignore [unsupported-operation]
                    parts[-1] += f"*{stride}"
                stride *= self.halide_vars[sym]
            self.body.writeline(f"{result_var} = {' + '.join(parts)}")
        elif reduction_type == "welford_reduce":
            # TODO(jansel): implement welford_reduce without fallback
            result_var = self.welford_reduce_fallback(dtype, value)
        else:
            combine_fn = get_reduction_combine_fn(reduction_type, acc_type)
            with V.set_ops_handler(AddParenHandler(HalideOverrides())):
                combine_str = combine_fn(result_var, value_str)  # type: ignore[arg-type]
            default_str = f"hl.cast({acc_type}, {halide_constant(default)})"
            self.body.writeline(f"{result_var} = {default_str}")
            self.body.writeline(f"{result_var} = {combine_str}")

        self.cse.reduction_cache[cache_key] = result_var
        return result_var