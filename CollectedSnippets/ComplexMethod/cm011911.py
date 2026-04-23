def store_output(
        self,
        indices: list[Any] | tuple[Any],
        val: str,
        mask: str | None = None,
        indent_width: int = 4,
        val_shape: tuple[str] | None = None,
        block_indexing: bool = False,
    ):
        """Stores the final output and appends any epilogue fusions if the buffer hasn't been optimized away.

        Args:
            indices (Union[List, Tuple]): The index for each dimension of the output. The dot product of
                these indices and output strides must match `val`.
            val (str): The value to store.
            mask (Optional[str]): An optional mask to use for the store operation. If provided, this mask
                will be applied to the store.
            indent_width (int): The number of spaces to use for indentation. This is used when the call to
                store_output is indented in the kernel definition.
            block_indexing (bool): Are the input indices presented as offsets for creating the block (e.g.
                inputs to TMA) or are they tensors that should be passed in directly.
        """
        subgraph_name = self._get_store_output_subgraph_name(
            next(self.store_output_ctr)
        )
        with self.create_subgraph_body(subgraph_name, clear_cse=True):
            assert isinstance(indices, (list, tuple))
            assert isinstance(val, str)
            assert isinstance(mask, (str, type(None)))
            assert isinstance(val_shape, (tuple, type(None)))
            assert isinstance(block_indexing, bool)
            assert self.template_mask is None
            indices = list(map(OpOverrides.paren, indices))
            index_symbols = [sympy.Symbol(x, integer=True) for x in indices]
            lengths = [
                V.graph.sizevars.simplify(s) for s in self.output_node.get_size()
            ]
            assert len(indices) == len(lengths)

            output_layout = self.output_node.get_layout()
            self.template_out = val
            if block_indexing:
                assert val_shape, "Blocking indexing requires passing in val_shape"
                assert len(val_shape) == 2, (
                    "Blocking indexing only supports 2D data at this time"
                )
                assert not mask, "Mask is not supported with blocking indexing"
                intermediate_lines: list[str] = []
                epilogue_index_symbols: list[sympy.Symbol] = []
                if self.tma_store:
                    val_shape_copy = list(val_shape)
                    for i, range_tree in enumerate(self.range_trees[:-1]):
                        name = range_tree.name
                        symbol = range_tree.symbol()
                        epilogue_index_symbols.append(symbol)
                        lookup_output = range_tree.lookup(sympy.S.One, lengths[i])
                        old_name = lookup_output.symbol()
                        lookup_output.set_name(name)
                        # Update var_list and var_range
                        range_tree.var_list[range_tree.var_list.index(old_name)] = (
                            symbol
                        )
                        range_val = range_tree.var_ranges[old_name]
                        del range_tree.var_ranges[old_name]
                        range_tree.var_ranges[symbol] = range_val
                        intermediate_lines.extend(
                            self._generate_index_from_tma_index(
                                name,
                                "xoffset" if name == "xindex" else "yoffset",
                                index_symbols[i],
                                val_shape[i],
                                i,
                                len(val_shape),
                                block_name=range_tree.symt.name,
                            )
                        )
                        # Generate the xmask and ymask
                        intermediate_lines.append(
                            self._generated_mask_for_tma(
                                name,
                                self.size(None, i),
                                "xmask" if name == "xindex" else "ymask",
                            )
                        )
                        # Update the val_shape information to use consistent naming
                        # after the remapping.

                        val_shape_copy[i] = range_tree.symt.name
                    # pyrefly: ignore [bad-assignment]
                    val_shape = tuple(val_shape_copy)
                else:
                    mask_vars: list[str] = []
                    for i, (index, shape) in enumerate(zip(index_symbols, val_shape)):
                        index_name = self._gen_tmp_var()
                        offset_name = self._gen_tmp_var()
                        intermediate_lines.extend(
                            self._generate_index_from_tma_index(
                                index_name,
                                offset_name,
                                index,
                                shape,
                                i,
                                len(index_symbols),
                            )
                        )
                        epilogue_index_symbols.append(
                            sympy.Symbol(index_name, integer=True)
                        )
                        mask_name = self._gen_tmp_var()
                        intermediate_lines.append(
                            self._generated_mask_for_tma(
                                index_name,
                                self.size(None, i),
                                mask_name,
                            )
                        )
                        mask_vars.append(mask_name)
                    final_mask_var = self._gen_tmp_var()
                    final_mask_rhs = " & ".join(
                        f"{mask_name}" for mask_name in mask_vars
                    )
                    intermediate_lines.append(f"{final_mask_var} = {final_mask_rhs}")
                    self.template_mask = final_mask_var
                index_symbols = epilogue_index_symbols
                contiguous_index = sympy_dot(output_layout.stride, index_symbols)
                if not self.tma_store:
                    # Convert to just use xindex.
                    contiguous_index = self.rename_indexing(contiguous_index)
                    intermediate_lines.append(f"xindex = {texpr(contiguous_index)}")
                    self.range_trees[0].lookup(
                        sympy.S.One, sympy_product(lengths)
                    ).set_name("xindex")
                index_symbols = epilogue_index_symbols
                output_index = contiguous_index
                # Write out the intermediate lines
                for line in intermediate_lines:
                    self.body.writeline(line)
            else:
                assert not self.tma_store, "TMA store requires block indexing"
                contiguous_index = self._setup_contiguous_index_state(
                    indices, index_symbols, lengths, mask
                )
                output_index = self.output_node.get_layout().make_indexer()(
                    index_symbols
                )
                output_index = self.rename_indexing(output_index)
                if output_index == contiguous_index:
                    output_index = sympy.Symbol("xindex", integer=True)

            self.template_out_shape = val_shape if val_shape else val
            acc_dtype = (
                triton_type_to_torch(self.meta["ACC_TYPE"])
                if "ACC_TYPE" in self.meta
                else torch.float32
            )
            epilogue_args = [
                V.kernel.cse.namedvar(val, dtype=acc_dtype, shape=val_shape)
            ]
            for input_node in itertools.chain(
                self.input_nodes[: self.prefix_args],
                self.input_nodes[len(self.input_nodes) - self.suffix_args :],
            ):
                input_node.freeze_layout()
                epilogue_arg = V.kernel.cse.generate(
                    self.compute,
                    input_node.make_loader()(index_symbols),
                    dtype=acc_dtype,
                    shape=input_node.get_size(),
                )
                epilogue_args.append(epilogue_arg)
                # We update frozen_layouts_cnt in order to replay this function on a cache hit.
                self.frozen_layouts_cnt += 1

            V.ops.store(
                self.output_node.get_name(),
                output_index,
                self.epilogue_fn(*epilogue_args),
                mode="tma" if self.tma_store else None,
            )
            self.codegen_body()

        return self._register_hook(
            subgraph_name, self._make_codegen_hook(subgraph_name, indent_width)
        )