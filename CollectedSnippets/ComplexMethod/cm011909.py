def modification(
        self,
        subgraph_number: int,
        output_name: str | None,
        mask: str | None = None,
        input_shapes: dict[str, tuple[str, ...]] | None = None,
        **fixed_inputs,
    ) -> str:
        """This creates a modification function for a subgraph.
        To use this inside a template, the first argument should specify which subgraph to codegen for

        Args:
            subgraph_number (int): The index of the subgraph in self.subgraphs
            output_name (Optional[str]): The name of the output variable to store the result in
            mask (Optional[str]): An optional mask to use for the store operation. If provided, this mask
                will be applied to the store.
            input_shapes (Optional[dict[str, tuple[str, ...]]]): Optional mapping of input names to their
                block shapes. Used for proper shape propagation during codegen.
        """
        num = 0
        out = None
        scatters = []
        while f"mod_{subgraph_number}_{num}" in self.subgraph_bodies:
            num += 1
        with self.create_subgraph_body(f"mod_{subgraph_number}_{num}"):
            subgraph = self._get_subgraph(subgraph_number)
            modification_handler = ModificationWrapper(
                self, subgraph_number, fixed_inputs, mask, input_shapes
            )
            with V.set_ops_handler(modification_handler):
                assert isinstance(subgraph, (ir.ComputedBuffer, list)), (
                    f"Expected the subgraph to be a ComputedBuffer or a List[ComputedBuffer], got {type(subgraph)}"
                )
                # Handle scatter stores
                if isinstance(subgraph, list):
                    for scatter_graph in subgraph:
                        scatters.append(self._handle_scatter_graph(scatter_graph))
                elif isinstance(subgraph.data, ir.InputBuffer):
                    out = subgraph.data.make_loader()(())
                else:
                    out = subgraph.data.inner_fn(())

            self.codegen_body()
            if output_name is not None:
                assert isinstance(output_name, str)
                assert out is not None
                self.body.writeline(f"{output_name} = {out.value}")
            else:
                assert out is None
                for scatter in scatters:
                    self.body.writeline(str(scatter))

            body_val = self.body.getvalue()
            self.cse.invalidate(OrderedSet())
            return body_val