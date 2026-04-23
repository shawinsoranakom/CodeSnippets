def codegen_prologues_in_subgraphs(
        self, buf_name_to_prologue_group, prologue_preserves_zero_mask_fn
    ):
        """Run prologue codegen in each load-input subgraph body."""
        for input_name, buffer in self.named_input_nodes.items():
            subgraph_name = f"<LOAD_INPUT_{input_name}>"
            prologue_group = buf_name_to_prologue_group.get(buffer.get_name(), [])
            if not prologue_group:
                continue
            can_codegen_without_upcast = all(
                p_n.can_codegen_without_upcasts() for p_n in prologue_group
            )
            with config.patch(
                "triton.codegen_upcast_to_fp32", not can_codegen_without_upcast
            ):
                with self.set_subgraph_body(subgraph_name):
                    for prologue_node in prologue_group:
                        if (
                            len(prologue_node.get_buffer_names()) == 1
                            and len(prologue_group) == 1
                        ):
                            if prologue_preserves_zero_mask_fn(prologue_node):
                                self.prologue_fused_inputs_preserve_zero |= (
                                    prologue_node.get_buffer_names()
                                )
                        prologue_node.codegen(
                            self.split_and_set_ranges(prologue_node.get_ranges())
                        )
                    self.cse.invalidate(OrderedSet())