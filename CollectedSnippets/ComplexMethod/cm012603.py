def store_reduction(
        self,
        name: str,
        index: sympy.Expr,
        value: CSEVariable,
    ):
        assert self.inside_reduction
        self.inside_reduction = False
        dtype = V.graph.get_dtype(name)
        indexing = self.indexing(
            index,
            block_ptr=True,
            tma_compatibility_checker=self.tma_compatibility_checker_cls(
                kernel=self,
                dtype=dtype,
                for_store=True,
                force=False,
            ),
        )
        self.inside_reduction = True
        var = self.args.output(name)

        exit_stack = contextlib.ExitStack()
        if self.cooperative_reduction:
            exit_stack.enter_context(
                self.guard_cooperative_store(name, self.post_loop_store)
            )

        self._handle_pdl_before_access(self.post_loop_store, var)

        if isinstance(indexing, (BlockPtrOptions, TensorDescriptorOptions)):
            self.post_loop_store.writeline(
                DeferredLine(
                    name,
                    self.codegen_block_ptr_store_line(
                        name,
                        indexing,
                        indexing.format(var),
                        value,
                        f", boundary_check={indexing.boundary_check()!r}",
                    ),
                )
            )
        else:
            assert isinstance(indexing, IndexingOptions)

            indexing_str = indexing.index_str
            if (
                is_sympy_integer_like(index)
                and value.shape is not None
                and not all(str(x) == "1" for x in value.shape)
            ):
                value_shape = ", ".join(map(str, value.shape))
                indexing_str += f".broadcast_to({value_shape})"

            self.post_loop_store.writeline(
                DeferredLine(
                    name,
                    f"tl.store({var} + ({indexing_str}), {value}, {indexing.mask_str})",
                )
            )

        exit_stack.close()