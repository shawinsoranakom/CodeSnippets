def scan(
        self,
        dtypes: tuple[torch.dtype, ...],
        combine_fn: Callable[
            [tuple[CSEVariable, ...], tuple[CSEVariable, ...]], tuple[CSEVariable, ...]
        ],
        values_orig: tuple[CSEVariable, ...],
    ) -> tuple[CSEVariable, ...]:
        assert self.inside_reduction
        assert len(dtypes) == len(values_orig)
        values: list[HalideCSEVariable] = []
        all_used_dims = OrderedSet[sympy.Symbol]()

        for value in values_orig:
            assert isinstance(value, HalideCSEVariable) and value.used_dims is not None
            if OrderedSet(value.used_dims) & OrderedSet(self.reduction_renames):
                values.append(value)
            else:
                values.append(
                    self.genfunc(
                        f"{value}",
                        [*value.used_dims, [*self.reduction_renames][:1]],
                        shape=value.shape,
                    )
                )
            all_used_dims.update(value.used_dims)
        result_var = self.newfunc(self.sort_used_dims(all_used_dims))
        assert result_var.used_dims and OrderedSet(result_var.used_dims) & OrderedSet(
            self.reduction_renames
        )
        initial = [
            f"hl.cast({halide_acc_type(dtype)}, {value})"
            for dtype, value in zip(dtypes, values)
        ]

        length = self.kexpr(self.rename_indexing(self.range_trees[-1].numel))
        scan_dom = f"{result_var.name}_rdom"
        scan = f"{scan_dom}.x"
        self.body.writeline(f"{scan_dom} = hl.RDom([hl.Range(1, {length})])")

        assert len(self.reduction_renames) == 1, (
            "multi-dimensional scan not implemented"
        )
        (scan_var,) = [*self.reduction_renames]  # type: ignore[misc]
        scan_renames_cur = {scan_var: sympy_index_symbol(scan)}
        scan_renames_pri = {scan_var: sympy_index_symbol(scan) - 1}

        if len(values) == 1:

            def maybe_tuple(x):
                return x[0]

            read_left = [result_var.subs_str(scan_renames_pri)]
            read_right = [result_var.subs_str(scan_renames_cur)]
        else:

            def maybe_tuple(x):
                return f"hl.Tuple([{', '.join(x)}])"

            read_left = [
                result_var.subs_str(scan_renames_pri) + f"[{i}]"
                for i in range(len(values))
            ]
            read_right = [
                result_var.subs_str(scan_renames_cur) + f"[{i}]"
                for i in range(len(values))
            ]

        self.body.writeline(f"{result_var} = {maybe_tuple(initial)}")

        # Disable CSE for update fn
        with V.set_ops_handler(AddParenHandler(HalideOverrides())):
            combine_str = combine_fn(read_left, read_right)  # type: ignore[arg-type]
        self.body.writeline(
            f"{result_var.subs_str(scan_renames_cur)} = {maybe_tuple(combine_str)}"
        )

        if len(values) == 1:
            return (result_var,)

        unpack_vars = [self.newfunc(self.sort_used_dims(all_used_dims)) for _ in values]
        for i, v in enumerate(unpack_vars):
            self.body.writeline(f"{v} = {result_var}[{i}]")
        return tuple(unpack_vars)