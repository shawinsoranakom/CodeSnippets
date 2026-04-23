def sort(
        self,
        dtypes: tuple[torch.dtype, ...],
        values: tuple[CSEVariable, ...],
        stable: bool,
        descending: bool,
    ) -> tuple[CSEVariable, ...]:
        assert self.inside_reduction
        assert not self.cooperative_reduction, "TODO"
        masks = OrderedSet(f"{tree.prefix}mask" for tree in self.range_trees)
        self.filter_masks(masks)
        masks = sorted(masks)
        assert not self._load_mask, "ops.sort not supported inside ops.masked"
        assert self.persistent_reduction, (
            "ops.sort is only supported in persistent reductions"
        )

        cse_compute = functools.partial(self.cse.generate, self.compute)
        dim = self.triton_tensor_ndim() - self.num_reduction_dims

        dtypes = tuple(upcast_compute_type(dtype) for dtype in dtypes)
        assert len(dtypes) == len(values)
        broadcasted_values = [
            cse_compute(
                f"tl.broadcast_to({value}, {self.dense_size_str()})",
                dtype=dtypes[i],
                shape=tuple(self.dense_size_list()),
            )
            for i, value in enumerate(values)
        ]

        def csv(values):
            return " ".join(f"{value}," for value in values)

        def cse_multiple(line, broadcasted_values, masks, dtypes):
            n = len(broadcasted_values)
            cache_keys = [f"{line}, {i}, {masks}" for i in range(n)]
            if all(self.cse.contains(cache_key) for cache_key in cache_keys):
                return [self.cse.get(cache_key) for cache_key in cache_keys]
            result_vars = [
                self.cse.newvar(dtype=dtype, shape=value.shape)
                for dtype, value in zip(dtypes, broadcasted_values)
            ]  # type: ignore[attr-defined]
            self.compute.writeline(
                f"{csv(result_vars)} = {line}",
            )
            for result_var, cache_key in zip(result_vars, cache_keys):
                if masks:
                    result_var.mask_vars = masks  # type: ignore[attr-defined]
                self.cse.put(cache_key, result_var)
            return tuple(result_vars)

        assert self.range_trees[-1].is_reduction
        rnumel = "None" if self._has_constant_mask(self.range_trees[-1]) else "rnumel"

        if len(values) == 2:
            line = (
                f"triton_helpers.sort_with_index({broadcasted_values[0]}, {broadcasted_values[1]},"
                f" {rnumel}, {dim}, stable={stable}, descending={descending})"
            )
            result_vars = cse_multiple(line, broadcasted_values, masks, dtypes)
        else:
            raise AssertionError("Unhandled sort")

        for result_var, input_var in zip(result_vars, values):
            result_var.mask_vars = masks  # type: ignore[attr-defined]
            result_var.bounds = input_var.bounds

        return tuple(result_vars)