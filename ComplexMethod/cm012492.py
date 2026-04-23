def scan(self, dtypes, combine_fn, values):
        """
        Perform an associative scan on 'values'.
        """
        import triton.language as tl

        (dtype,) = dtypes
        (value,) = values

        compute_type = triton_compute_type(dtype)
        compute_type_triton = getattr(tl, compute_type[3:])

        element_nbits = compute_type_triton.primitive_bitwidth

        scratch_type = "tl.uint32" if element_nbits <= 16 else "tl.uint64"
        scratch_type_triton = getattr(tl, scratch_type[3:])
        scratch_elems_per_block = 3 if element_nbits == 64 else 1
        scratch_nbytes_per_block = scratch_elems_per_block * (
            scratch_type_triton.primitive_bitwidth // 8
        )

        cse_load = functools.partial(self.cse.generate, self.loads, dtype=dtype)
        cse_compute = functools.partial(self.cse.generate, self.compute)

        assert len(self.numels) == 2, "Unexpected tiling"
        min_rblock = config.triton.min_split_scan_rblock
        reduction_numel = sympy_product(
            numel
            for prefix, numel in self.numels.items()
            if prefix_is_reduction(prefix)
        )
        pointwise_numel = sympy_product(
            numel
            for prefix, numel in self.numels.items()
            if not prefix_is_reduction(prefix)
        )
        max_blocks = pointwise_numel * CeilDiv(reduction_numel, min_rblock)
        nbytes = scratch_nbytes_per_block * max_blocks
        scratch_base: str | TritonCSEVariable
        scratch_base, _, offset = self.args.workspace(nelem=nbytes, zero_fill=True)
        if offset != 0:
            scratch_base = cse_load(
                f"{scratch_base} + {self.index_to_str(offset)}", shape=()
            )
        runtime_rblocks = cse_load(
            f"tl.num_programs({self.range_trees[-1].index})", shape=()
        )
        scratch_base = cse_load(
            f"{scratch_base}.to(tl.pointer_type({scratch_type})) + xoffset * "
            f"{scratch_elems_per_block} * {runtime_rblocks}",
            shape=(),
        )

        masks = OrderedSet(f"{tree.prefix}mask" for tree in self.range_trees)
        self.filter_masks(masks)
        assert not self._load_mask, "ops.scan not supported inside ops.masked"

        value = cse_compute(
            f"{value}.to({compute_type})",
            dtype=dtype,
            shape=value.shape,
        )
        value = cse_compute(
            f"tl.broadcast_to({value}, {self.dense_size_str()})",
            dtype=dtype,
            shape=self.dense_size_list(),
        )

        combine_helper_fn = self._lift_helper(combine_fn, (value,), (dtype,))
        dim = self.triton_tensor_ndim() - 1
        assert dim == 0, ""
        shape = list(self.dense_size_list())
        del shape[dim]

        block_sum = cse_compute(
            f"tl.reduce({value}, {dim}, {combine_helper_fn})",
            dtype=dtype,
            shape=shape,
        )
        exclusive_prefix = self.cse.newvar(
            dtype=dtype,
            shape=shape,
        )
        if element_nbits == 64:
            self.compute.splice(
                f"""
                {exclusive_prefix} = triton_helpers.exclusive_scan_decoupled_lookback_64(
                    {scratch_base},
                    {block_sum},
                    {self.iteration_ranges_get_pid(self.range_trees[-1])},
                    {combine_helper_fn},
                )
                """,
                strip=True,
            )

        else:
            assert element_nbits <= 32
            value_as_uint_dtype = f"tl.uint{element_nbits}"

            self.compute.splice(
                f"""
                {exclusive_prefix} = triton_helpers.exclusive_scan_decoupled_lookback(
                    {scratch_base},
                    {block_sum},
                    {self.iteration_ranges_get_pid(self.range_trees[-1])},
                    {combine_helper_fn},
                    DTYPE_VALUE_AS_UINT={value_as_uint_dtype},
                    DTYPE_PACK={scratch_type},
                )
                """,
                strip=True,
            )
        # Compute final cumsum
        block_scan = cse_compute(
            f"tl.associative_scan({value}, {dim}, {combine_helper_fn})",
            dtype=dtype,
            shape=shape,
        )
        combined_result = cse_compute(
            f"{combine_helper_fn}({exclusive_prefix}, {block_scan})",
            dtype=dtype,
            shape=shape,
        )
        return (
            cse_compute(
                f"tl.where(roffset == 0, {block_scan}, {combined_result})",
                dtype=dtype,
                shape=block_scan.shape,
            ),
        )