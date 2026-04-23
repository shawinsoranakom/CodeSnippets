def load_input(
        self,
        input_name: str,
        output_name: str,
        indices: list[Any] | tuple[Any],
        mask: str | None = None,
        other: float | int | None = 0.0,
        indent_width: int = 4,
        index_shape: tuple[str] | None = None,
    ):
        """Loads an input and applies any necessary preprocessing or masking.

        Args:
            input_name (str): The name of the input to load.
            indices (Union[List, Tuple]): The index for each dimension of the input.
            val (str): The name of the variable to store the loaded value.
            mask (Optional[str]): An optional mask to use for the load operation.
            other (Optional[Union[float, int]]): The value to use for masked elements. Default is 0.0.
            indent_width (int): The number of spaces to use for indentation.
        """

        input_node = self.named_input_nodes[input_name]
        if not self.prologue_loads_all_inputs:
            self.prologue_supported_inputs.add(input_node.get_name())

        tilings = (sympy_product(input_node.get_size()), sympy.Integer(1))
        groups = {
            "x": tilings[0],
            "r0_": tilings[1],
        }

        range_trees = self.construct_range_trees(
            pid_cache=None,
            inside_reduction=False,
            is_reduction=False,
            numels=groups,
            no_x_dim=False,
        )
        load_code = None

        with self.create_subgraph_body(f"<LOAD_INPUT_{input_name}>"):
            assert isinstance(indices, (list, tuple))
            assert isinstance(output_name, str)
            assert isinstance(mask, (str, type(None)))
            self.range_trees = range_trees
            self.numels = {k: V.graph.sizevars.simplify(v) for k, v in groups.items()}
            indices = list(map(OpOverrides.paren, indices))
            index_symbols = [sympy.Symbol(x, integer=True) for x in indices]

            lengths = [V.graph.sizevars.simplify(s) for s in input_node.get_size()]
            assert len(indices) == len(lengths)

            # MM templates use out-of-bounds wrapping (e.g. `rm % M`) so no mask
            # is needed on the load.  Pass "None" when mask is unset to override
            # the mask that would otherwise be inherited.
            contiguous_index = self._setup_contiguous_index_state(
                indices,
                index_symbols,
                lengths,
                mask=mask if mask is not None else "None",
            )
            self.template_out_shape = index_shape if index_shape else "xindex"
            self.cse.invalidate(OrderedSet())

            template_mask = self.template_mask

            class StoreOutputSubstitution(V.WrapperHandler):  # type: ignore[name-defined]
                name = "StoreOutputSubstitution"

                def store(
                    self,
                    name: str,
                    index: sympy.Expr,
                    value: "CSEVariable",
                    mode: "StoreMode" = None,
                ):
                    V.kernel.store_buffer_names.add(name)
                    V.kernel.cse.store_cache[name] = value
                    if name in V.kernel.prologue_fused_inputs:
                        # We load masked out values with 0, then apply a prologue.
                        # The masked out values may not necessariliy be 0 any more
                        # so we need to reapply the mask.
                        value_dtype = value.dtype
                        value_str = str(value)
                        if template_mask != "None" and (
                            name not in V.kernel.prologue_fused_inputs_preserve_zero
                            or other != 0
                        ):
                            value_str = (
                                f"tl.where({template_mask}, {value_str}, {other})"
                            )

                        if value_dtype != V.graph.get_buffer(name).dtype:
                            value_str = f"{value_str}.to({triton_type(V.graph.get_buffer(name).dtype)})"

                        # TODO: we should have intermediary var shapes
                        V.kernel.compute.writeline(
                            f"{output_name} = {value_str}.broadcast_to(xindex.shape)"
                        )

            # pyrefly: ignore [bad-assignment]
            self.ops_handler = StoreOutputSubstitution

            input_node = self.named_input_nodes[input_name]
            if isinstance(input_node.layout, ir.FlexibleLayout):
                # This will set a layout constraint on the template
                self.get_stride_and_maybe_freeze_layout(input_node)
                with patch.object(ir.FlexibleLayout, "allow_indexing", True):
                    output_index = input_node.make_indexer()(index_symbols)
            else:
                output_index = input_node.make_indexer()(index_symbols)

            # in def_kernel above we define the inputs with the storage offset adjusted
            # creating the load in input_node.make_indexer() will also adjust by storage offset
            # so subtract here to not double increment
            if not V.graph.sizevars.statically_known_equals(
                input_node.layout.offset, 0
            ):
                output_index = output_index - self.rename_indexing(
                    input_node.get_layout().offset
                )

            output_index = self.rename_indexing(output_index)

            if output_index == contiguous_index:
                output_index_str = "xindex"
            else:
                out_indexing = self.indexing(
                    output_index,
                    copy_shape=self.template_out_shape,
                    override_mask=self.template_mask,
                )
                from .codegen.triton import IndexingOptions

                assert isinstance(out_indexing, IndexingOptions)
                output_index_str = (
                    f"({out_indexing.index_str}).broadcast_to(xindex.shape)"
                )

            # Generate load code
            load_code = f"{output_name} = tl.load({input_name} + ({output_index_str})"

            if mask:
                load_code += f", mask={mask}, other={other})"
            else:
                load_code += ")"

        hook_key = f"<LOAD_INPUT_{input_name}>"

        def hook():
            with self.set_subgraph_body(hook_key):
                self.cse.invalidate(OrderedSet())
                self.codegen_body()
                self.cse.invalidate(OrderedSet())
                if input_node.get_name() not in self.prologue_fused_inputs:
                    assert load_code is not None
                    self.body.writeline(load_code)

                result = self.body.getvalue()
                if indent_width:
                    result = textwrap.indent(result, " " * indent_width)
                return result.strip()

        return self._register_hook(hook_key, hook)