def store(
        self, name: str, index: sympy.Expr, value: CSEVariable, mode: StoreMode = None
    ) -> None:
        """
        store the 'value' to the memory location 'name', offset by some indexing expression 'index'.
        """

        var = self.args.output(name)
        original_index = index
        dtype = V.graph.get_dtype(name)

        tma_compatibility_checker = None
        if mode is None or mode == "tma":
            force = mode == "tma"
            tma_compatibility_checker = self.tma_compatibility_checker_cls(
                self,
                dtype,
                for_store=True,
                force=force,
            )
        indexing = self.indexing(
            index,
            dense_indexing=True,
            block_ptr=mode is None,
            tma_compatibility_checker=tma_compatibility_checker,
            mask_constant_index=mode == "atomic_add",
        )

        if isinstance(indexing, IndexingOptions) and self._has_stride1_on_rdim(
            indexing.index
        ):
            self.stores_with_contiguous_rdim.append(name)

        # Guard against write-after-read corruption in triton.
        # See # https://github.com/triton-lang/triton/issues/1615
        # This triton bug means that a load which is broadcasted over multiple
        # warps may see the result of a store that happens later in the triton
        # program. The workaround is to add a barrier before storing, which
        # enforces that all warps have already read the data.
        is_inplace = name in self.args.inplace_buffers
        is_broadcasted = self.is_broadcasted(original_index)
        if is_inplace and is_broadcasted:
            self.stores.writeline(DeferredLine(name, "tl.debug_barrier()"))

        if isinstance(indexing, (BlockPtrOptions, TensorDescriptorOptions)):
            block_descriptor, other = self.codegen_block_ptr(name, var, indexing)
            # block_ptr / tma descriptor stores don't do implicit casting
            line = self.codegen_block_ptr_store_line(
                name, indexing, block_descriptor, value, other
            )
        elif mode is None:
            # If indexing is an integer and value has block shape larger than one,
            # broadcasting fails. So, we manually broadcast indexing to the value shape.
            # Without broadcast :
            # tl.store(out_ptr0 + (tl.full([1, 1], 0, tl.int32)), tmp4, xmask) # Fail
            #
            # With broadcast:
            # tl.store(out_ptr0 + (tl.full([1, 1], 0, tl.int32).broadcast_to((XBLOCK,1)), tmp4, xmask)
            indexing_str = indexing.index_str
            if is_sympy_integer_like(index):
                if self.is_combo_kernel:
                    # In combo kernels, broadcast pointer to match mask shape
                    indexing_str += f".broadcast_to({self.dense_size_str()})"
                elif value.shape is not None and not all(
                    str(x) == "1" for x in value.shape
                ):
                    value_shape = ", ".join(map(str, value.shape))
                    indexing_str += f".broadcast_to({value_shape})"
            line = f"tl.store({var} + ({indexing_str}), {value}, {indexing.mask_str})"
        elif mode == "atomic_add":
            self.atomic_add_found = True
            indexing_str = indexing.index_str
            if (
                is_sympy_integer_like(index)
                and value.shape is not None
                and not all(str(x) == "1" for x in value.shape)
            ):
                value_shape = ", ".join(map(str, value.shape))
                indexing_str += f".broadcast_to({value_shape})"
            line = f"tl.atomic_add({var} + ({indexing_str}), {value}, {indexing.mask_str}, sem='relaxed')"
        else:
            raise NotImplementedError(f"store mode={mode}")

        exit_stack = contextlib.ExitStack()
        if not self.inside_reduction and self.cooperative_reduction:
            exit_stack.enter_context(self.guard_cooperative_store(name, self.stores))

        self._handle_pdl_before_access(self.stores, name, consider_reads=True)
        self.stores.writeline(DeferredLine(name, line))

        if not self.inside_reduction:
            self.outside_loop_vars.add(value)

        exit_stack.close()