def allocate(self) -> None:
        assert self.node is not None
        if not self.node.should_allocate():
            return

        if (
            self.node.get_inputs_that_alias_output()
            or self.node.get_mutation_names()
            or isinstance(self.node.get_output_spec(), ir.CommBufferLayout)
        ):
            V.graph.wrapper_code.codegen_allocation(self.node)
            return

        # hacky check for if V.kernel is a real kernel or NullHandler
        if (
            hasattr(V.kernel, "args")
            and self.get_name() in V.kernel.inplace_update_buffers
        ):
            input_buffer: ir.DonatedBuffer | ir.Buffer
            input_buffer_name = V.kernel.inplace_update_buffers[self.get_name()]
            if input_buffer_name in self.scheduler.name_to_donated_buffer:
                input_buffer = self.scheduler.name_to_donated_buffer[
                    input_buffer_name
                ].node
            else:
                input_buffer = self.scheduler.name_to_buf[input_buffer_name].node
            V.graph.wrapper_code.codegen_inplace_reuse(
                input_buffer,
                self.node,
            )
        else:
            V.graph.wrapper_code.codegen_allocation(self.node)