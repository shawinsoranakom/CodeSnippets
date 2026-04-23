def _setup_epilogue_hook(self, output_buf=None, output_param=None):
        store_idx = next(self.store_output_ctr)
        subgraph_name = self._get_store_output_subgraph_name(store_idx)
        if output_buf is None:
            self.subgraph_bodies[subgraph_name] = SubgraphInfo(body=IndentedBuffer())
            self.render_hooks[subgraph_name] = lambda: ""
            return

        n_dims = len(self._template_buffer.get_size())
        indices = [f"x_epilogue{store_idx}_{d}" for d in range(n_dims)]
        val = f"_kernel_val_{store_idx}"
        mask = f"_tile_mask_{store_idx}"

        buf = output_buf
        node = V.graph.get_buffer(buf) if buf else None
        output_size = (
            list(node.get_size())
            if node is not None
            else list(self.output_node.get_size())
        )
        self._make_independent_subgraph(subgraph_name, sympy_product(output_size))
        with self.set_subgraph_body(subgraph_name):
            indices = list(map(OpOverrides.paren, indices))
            index_symbols = [sympy.Symbol(x, integer=True) for x in indices]
            lengths = [V.graph.sizevars.simplify(s) for s in output_size]
            assert len(indices) == len(lengths)
            self.template_out = val
            self._setup_contiguous_index_state(
                indices,
                index_symbols,
                lengths,
                mask,
                xindex_name=f"x_epilogue{store_idx}_index",
            )
            self.template_out_shape = val

            # Set up CSE state for epilogue codegen
            block_shape = tuple(
                f"{rt.prefix.upper()}BLOCK"
                for rt in self.range_trees
                if not rt.is_reduction
            )
            if not block_shape:
                block_shape = ("XBLOCK",)
            self.cse.store_cache[buf] = self.cse.namedvar(
                val, dtype=torch.float32, shape=block_shape
            )
            assert output_param is not None
            self.args.output_buffers[buf] = output_param

        self.render_hooks[subgraph_name] = self._make_codegen_hook(subgraph_name)