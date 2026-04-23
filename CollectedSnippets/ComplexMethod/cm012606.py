def codegen_body(self):
        """
        Concat output code from index_code, loads, compute, stores,
        suffix into self.body.

        For pointwise kernels, this is called just once at the end.

        For reduction kernels, this generates a loop over the reduction
        axis.
        """
        if not (
            self.indexing_code
            or self.loads
            or self.stores
            or self.compute
            or self.post_loop_combine
            or self.post_loop_store
        ):
            return

        loop_trees = [tree for tree in self.range_trees if tree.is_loop]
        if self.mix_order_reduction:
            assert self.persistent_reduction, (
                "Mix order reduction requires persistent reduction"
            )
            accumname2var = {}
            for idx, partial_accum in enumerate(self.saved_partial_accumulate):
                reduction_type = partial_accum.reduction_type
                default = ir.Reduction.default_accumulator(reduction_type, torch.float)
                default = self._map_tuple_or_scalar(constant_repr, default)
                name = f"accum{idx}"
                self.body.writeline(
                    f"{name} = tl.full([R0_BLOCK], {default}, tl.float32)[None, :]"
                )
                accumname2var[name] = self.cse.namedvar(
                    name, dtype=torch.float, shape=("1", "R0_BLOCK")
                )
            self.body.writeline("split_size = min(RSPLIT_SIZE, xnumel - xoffset)")
            self.body.writeline(
                "for _ in tl.range(0, split_size, XBLOCK, num_stages=NUM_STAGES):"
            )
            with self.body.indent(offset=1):
                # generate xmask if it's not constant
                if not self._has_constant_xmask():
                    entry = self.range_trees[0]
                    assert entry.prefix == "x"
                    x = entry.prefix
                    self.body.writeline(f"{x}mask = {entry.name} < {x}numel")
                self.body.splice(self.indexing_code)
                self.body.writelines(
                    [
                        "xindex += XBLOCK",
                    ]
                )
                self.body.splice(self.loads)
                self.body.splice(self.compute)
                self.body.splice(self.stores)
                self.body.splice(self.post_loop_store)

                # no need to sum if XBLOCK == 1, or does that matter?
                for idx, partial_accum in enumerate(self.saved_partial_accumulate):
                    var = partial_accum.value
                    name = f"accum{idx}"
                    combine_fn = ir.get_reduction_combine_fn(
                        partial_accum.reduction_type, torch.float
                    )
                    triton_reduction_function = get_triton_reduction_function(
                        partial_accum.reduction_type,
                    )
                    newval = self.cse.generate(
                        self.body,
                        f"{triton_reduction_function}({var}, 0)",
                        dtype=var.dtype,
                        shape=("R0_BLOCK",),
                    )
                    import unittest

                    with unittest.mock.patch.object(self, "compute", self.body):
                        updated = combine_fn(
                            accumname2var[name],
                            newval,
                        )
                    self.body.writeline(f"{name} = {updated}")

            for idx in range(len(self.saved_partial_accumulate)):
                self.body.writeline(
                    f"tl.store(ws_ptr + (tl.program_id(0) + {idx} * tl.num_programs(0)) * r0_numel + r0_index, accum{idx}, r0_mask)"
                )

        elif self.inside_reduction and len(loop_trees) > 0:
            # Write the loop headers.
            for level, tree in enumerate(loop_trees):
                with self.body.indent(offset=level):
                    prefix = tree.prefix
                    loop_start = "rsplit_start" if self.cooperative_reduction else "0"
                    loop_end = (
                        "rsplit_end" if self.cooperative_reduction else f"{prefix}numel"
                    )
                    # Conditionalize pipelining on HIP for Triton due to
                    # reports of numerical inaccuracies on older Triton
                    if torch.version.hip and get_triton_version() > (3, 2):
                        num_stages = ", num_stages = 2"
                    else:
                        num_stages = ""
                    self.body.writeline(
                        f"for {prefix}offset in tl.range({loop_start}, {loop_end}, {prefix.upper()}BLOCK{num_stages}):"
                    )
                with self.body.indent(offset=level + 1):
                    self.iteration_ranges_codegen_header(tree, self.body)

            # The innermost loop performs the reduction.
            with self.body.indent(offset=len(loop_trees)):
                self.codegen_reduction_indices(self.body)
                self.body.splice(self.indexing_code)
                self.body.splice(self.loads)
                self.body.splice(self.compute)
                self.body.splice(self.stores)

            # Write loop suffixes.
            for level, tree in reversed([*enumerate(loop_trees)]):
                with self.body.indent(offset=level + 1):
                    # Advance pointers at the end of each loop.
                    for block_ptr, advancement in self.pointer_advancements[
                        tree.symt
                    ].items():
                        # Subtract any advancements made in the previous loop level.
                        if level < len(loop_trees) - 1:
                            prev_tree = loop_trees[level + 1]
                            prev_advancements = self.pointer_advancements[
                                prev_tree.symt
                            ]
                            # block_ptr may not exist in the inner loop's advancements
                            # if its advancement was identity (zero) and was skipped
                            if block_ptr in prev_advancements:
                                prev_advancement = prev_advancements[block_ptr]
                                prev_block = TritonSymbols.get_block_size(prev_tree)
                                prev_num_iter = CeilDiv(prev_tree.numel, prev_block)
                                advancement = [
                                    cur - prev * prev_num_iter
                                    for cur, prev in zip(advancement, prev_advancement)
                                ]

                        self.body.writeline(
                            DeferredLine(
                                self.block_ptr_to_buffer[block_ptr],
                                f"{block_ptr} = tl.advance({block_ptr}, {V.kernel.index_to_str(advancement)})",
                            )
                        )

                # Invalidate any cache entries that came from inside the loop.
                self.cse.invalidate(self.outside_loop_vars)
                tree.cache_clear()
        else:
            self.body.splice(self.indexing_code)
            self.body.splice(self.loads)
            self.body.splice(self.compute)
            self.body.splice(self.stores)
        self.body.splice(self.post_loop_combine)
        if self.cooperative_reduction and (
            self.post_loop_combine or self.post_loop_store
        ):
            sem_ptr = f"{self.semaphores_name} + tl.program_id(1)"
            self.body.splice(
                f"""
                if HAS_RSPLIT:
                    triton_helpers.x_grid_barrier({sem_ptr})
                """,
                strip=True,
            )
            self.cooperative_reduction_workspace_cache.on_loop_end()
        if not self.mix_order_reduction:
            self.body.splice(self.post_loop_store)
        self.indexing_code.clear()
        self.loads.clear()
        self.compute.clear()
        self.stores.clear()
        self.post_loop_combine.clear()
        self.post_loop_store.clear()