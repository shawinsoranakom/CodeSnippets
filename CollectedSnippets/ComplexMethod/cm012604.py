def scan(
        self,
        dtypes: tuple[torch.dtype, ...],
        combine_fn: Callable[
            [tuple[CSEVariable, ...], tuple[CSEVariable, ...]], tuple[CSEVariable, ...]
        ],
        values: tuple[CSEVariable, ...],
    ) -> tuple[CSEVariable, ...]:
        """
        Perform an associative scan on 'values'.
        """
        assert self.inside_reduction
        assert not self.cooperative_reduction, "TODO"
        masks = OrderedSet(f"{tree.prefix}mask" for tree in self.range_trees)
        self.filter_masks(masks)
        masks = sorted(masks)
        assert not self._load_mask, "ops.scan not supported inside ops.masked"

        broadcasted_values = []
        accumulators = []

        dtypes = tuple(upcast_compute_type(dtype) for dtype in dtypes)
        cse_compute = functools.partial(self.cse.generate, self.compute)
        combine_helper_fn = self._lift_helper(combine_fn, values, dtypes)
        dim = self.triton_tensor_ndim() - self.num_reduction_dims

        for value, dtype in zip(values, dtypes):
            value_dtype = self.cse.generate(
                self.compute,
                f"{value}.to({triton_compute_type(dtype)})",
                dtype=dtype,
                shape=value.shape,
            )
            value = self.cse.generate(
                self.compute,
                f"tl.broadcast_to({value_dtype}, {self.dense_size_str()})",
                dtype=dtype,
                shape=tuple(self.dense_size_list()),
            )
            broadcasted_values.append(value)

            acc_type = triton_acc_type(dtype)

            if not self.persistent_reduction:
                reduced_size = self.dense_size_list()
                reduced_size[-1] = "1"
                accumulator = self.cse.newvar(dtype=dtype, shape=reduced_size)
                reduced_size_str = f"[{', '.join(reduced_size)}]"

                default = "float('nan')" if dtype.is_floating_point else "-1"
                self.body.writeline(
                    f"{accumulator} = tl.full({reduced_size_str}, {default}, {acc_type})"
                )

                accumulators.append(accumulator)

        def csv(values):
            return " ".join(f"{value}," for value in values)

        def cse_multiple(line, values, masks, dtypes):
            n = len(values)
            cache_keys = [f"{line}, {i}, {masks}" for i in range(n)]
            if all(self.cse.contains(cache_key) for cache_key in cache_keys):
                return [self.cse.get(cache_key) for cache_key in cache_keys]
            result_vars = [
                self.cse.newvar(dtype=dtype, shape=value.shape)
                for (dtype, value) in zip(dtypes, values)
            ]
            self.compute.writeline(
                f"{csv(result_vars)} = {line}",
            )
            for result_var, cache_key in zip(result_vars, cache_keys):
                if masks:
                    result_var.mask_vars = masks  # type: ignore[attr-defined]
                self.cse.put(cache_key, result_var)
            return tuple(result_vars)

        partial_scan_vars = cse_multiple(
            f"tl.associative_scan(({csv(broadcasted_values)}), {dim}, {combine_helper_fn})",
            broadcasted_values,
            masks,
            dtypes,
        )

        if not self.persistent_reduction:
            # tl.reduce doesn't work for non-commutative operators, so instead
            # of repeating the scan op as a reduction, we use sum to select the
            # last scan value
            def _partial_scan_shape(var):
                if var.shape is None:
                    return None
                else:
                    shape = list(var.shape)
                    shape[-1] = "1"
                    return shape

            partial_reduce_vars = [
                cse_compute(
                    f"triton_helpers.select_one(({partial_scan_var}), rbase == (RBLOCK - 1), dim=-1, keep_dims=True)",
                    dtype=upcast_compute_type(partial_scan_var.dtype),
                    shape=_partial_scan_shape(partial_scan_var),
                )
                for partial_scan_var in partial_scan_vars
            ]
            accs_next = combine_fn(tuple(accumulators), tuple(partial_reduce_vars))
            full_scan_vars = combine_fn(tuple(accumulators), partial_scan_vars)
            result_vars = [
                cse_compute(
                    f"tl.where(roffset > 0, {full_scan}, {partial_scan})",
                    dtype=partial_scan.dtype,
                    shape=partial_scan.shape,
                )
                for full_scan, partial_scan in zip(full_scan_vars, partial_scan_vars)
            ]
            for acc_next, accumulator, partial_reduce in zip(
                accs_next, accumulators, partial_reduce_vars
            ):
                self.compute.writeline(
                    f"{accumulator} = tl.where(roffset > 0, {acc_next}, {partial_reduce})"
                )
        else:
            result_vars = partial_scan_vars

        for result_var in result_vars:
            assert isinstance(result_var, TritonCSEVariable)
            result_var.mask_vars = OrderedSet(masks)

        return tuple(result_vars)