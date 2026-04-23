def free_buffers(self) -> None:
        """Free any buffers that are no longer needed"""
        for name in sorted(
            self.buffer_names_to_free
            - V.graph.removed_buffers
            - V.graph.wrapper_code.freed  # type: ignore[has-type]
        ):
            if name in self.name_to_buf:
                buf = self.name_to_buf[name]
                if buf.can_free():
                    V.graph.wrapper_code.codegen_free(buf.node)
            elif name in V.graph.graph_inputs:
                inp = V.graph.graph_inputs[name]
                if isinstance(inp, ir.TorchBindObject):
                    V.graph.wrapper_code.codegen_free(inp)
                elif isinstance(inp, (ir.GeneratorState, ir.OpaqueObjectState)):
                    continue
                else:
                    storage = inp.data
                    assert (
                        isinstance(storage, ir.StorageBox) and storage.is_input_buffer()
                    )
                    V.graph.wrapper_code.codegen_free(storage.data)

        self.buffer_names_to_free.clear()