def codegen_block_ptr(
        self,
        name: str,
        var: str,
        indexing: BlockPtrOptions | TensorDescriptorOptions,
        other="",
    ) -> tuple[str, str]:
        """Generate a block pointer or tensor descriptor for Triton kernel operations.

        This method creates either a block pointer (for regular Triton operations) or
        a tensor descriptor (for TMA operations) based on the indexing type. It handles
        caching and reuse of descriptors for performance optimization.

        Args:
            name: The name of the buffer/tensor being accessed
            var: The variable name for the pointer
            indexing: Block pointer options or tensor descriptor options containing
                     indexing information and boundary check settings
            other: Additional parameters string (e.g., padding options)

        Returns:
            A tuple containing:
            - block_descriptor: The generated block pointer or tensor descriptor variable name
            - other: Modified additional parameters string with boundary check options
        """
        check = indexing.boundary_check()
        if isinstance(indexing, TensorDescriptorOptions):
            if check and other:
                # The TMA API currently does not support padding values
                # but the default is zero
                assert other == ", other=0.0"
                other = ""
        else:
            if not check:
                # workaround https://github.com/triton-lang/triton/issues/2813
                other = ""
            elif other:
                assert other == ", other=0.0"
                other = f", boundary_check={check!r}, padding_option='zero'"
            else:
                other = f", boundary_check={check!r}"

        if (
            self.inside_reduction
            and self.range_trees[-1].is_loop
            and indexing.has_rindex()
        ) or indexing.can_lift:
            if indexing.can_lift and var in self.prologue_cache:
                # Check for epilogue subtiling to reuse the same
                # tensor descriptor.
                block_descriptor = self.prologue_cache[var]
            else:
                block_ptr_line = indexing.format(var, roffset=False)
                block_var = self.cse.try_get(block_ptr_line)

                # Early return if block descriptor already exists
                if block_var:
                    return str(block_var), other

                block_descriptor_id = next(self.block_ptr_id)
                if isinstance(indexing, BlockPtrOptions):
                    block_descriptor = f"block_ptr{block_descriptor_id}"
                else:
                    block_descriptor = f"tma_descriptor{block_descriptor_id}"
                named_var = self.cse.namedvar(
                    block_descriptor, dtype=torch.uint64, shape=[]
                )
                self.cse.put(block_ptr_line, named_var)

                line_body = DeferredLine(name, f"{block_descriptor} = {block_ptr_line}")
                if indexing.can_lift:
                    self.prologue.writeline(line_body)
                    # Cache the descriptor for epilogue subtiling
                    self.prologue_cache[var] = block_descriptor
                else:
                    self.body.writeline(line_body)

                if isinstance(indexing, BlockPtrOptions):
                    # Store for later use. If the buffer is removed the below advancements
                    # are no longer necessary
                    self.block_ptr_to_buffer[block_descriptor] = name

                    # Generate block pointer advancements, for later use.
                    for symt in TritonSymbols.reduction_types:
                        advance_offsets = indexing.advance_roffset(symt)

                        # Ignore identity advancements.
                        if all(
                            V.graph.sizevars.statically_known_equals(
                                offset, sympy.Integer(0)
                            )
                            for offset in advance_offsets
                        ):
                            continue

                        advancements = self.pointer_advancements[symt]
                        assert block_descriptor not in advancements, (
                            f"duplicate advancement for pointer '{block_descriptor}' at type '{symt}'"
                        )
                        advancements[block_descriptor] = advance_offsets
        else:
            block_descriptor = indexing.format(var)
        return block_descriptor, other