def _create_flattened_inputs(self) -> None:
        """Create new placeholder nodes for flattened inputs with proper fake tensors."""
        for i in range(len(self.flat_inputs)):
            placeholder = super().placeholder(f"arg_{i}", (), {})

            # Check if this user input (index i) maps to a graph placeholder
            if i in self.graph_input_order:
                # graph_input_order[i] gives us which graph placeholder this user input corresponds to
                graph_placeholder_idx = self.graph_input_order[i]
                if graph_placeholder_idx < len(self.placeholders):
                    orig_placeholder = self.placeholders[graph_placeholder_idx]
                    # Copy other metadata but not "val" yet
                    for key, value in orig_placeholder.meta.items():
                        if key != "val":
                            placeholder.node.meta[key] = value

            # Always ensure we have proper "val" metadata from fake tensor
            if self.fake_mode is not None and isinstance(
                self.flat_inputs[i], torch.Tensor
            ):
                placeholder.node.meta["val"] = self.fake_mode.from_tensor(
                    self.flat_inputs[i],
                    symbolic_context=StatelessSymbolicContext(
                        dynamic_sizes=[
                            (
                                DimDynamic.DYNAMIC
                                if d in self.flat_args_dynamic_dims[i]
                                else DimDynamic.STATIC
                            )
                            for d in range(len(self.flat_inputs[i].shape))
                        ],
                        constraint_sizes=[None] * len(self.flat_inputs[i].shape),
                    ),
                )
            elif hasattr(self.flat_inputs[i], "val"):  # _IntWrapper case
                placeholder.node.meta["val"] = self.flat_inputs[i].val
            else:
                placeholder.node.meta["val"] = self.flat_inputs[i]

            # pyrefly: ignore [unsupported-operation]
            self.new_input_nodes[i] = placeholder