def codegen_allocation(self, buffer: ir.Buffer):
        name = buffer.get_name()

        if (
            name in V.graph.removed_buffers
            or name in self.allocated
            or isinstance(buffer, (ir.DonatedBuffer, ir.SubgraphBuffer, ir.InputBuffer))
        ):
            return
        self.allocated.add(name)
        if (
            isinstance(
                buffer.get_defining_op(),
                (ir.ExternKernelAlloc, ir.MultiOutput),
            )
            and not buffer.should_allocate()
        ):
            return

        layout = buffer.get_output_spec()
        if isinstance(layout, ir.MutationLayoutSHOULDREMOVE):
            return
        if isinstance(layout, ir.NoneLayout):
            return
        if isinstance(layout, ir.NonOwningLayout):
            assert isinstance(layout.view, ir.ReinterpretView), (
                f"unexpected {type(layout.view)}: {layout.view}"
            )
            box = layout.view.data
            assert isinstance(box, ir.StorageBox), type(box)
            input_buffer = box.data
            assert isinstance(input_buffer, (ir.Buffer, ir.ReinterpretView)), type(
                input_buffer
            )
            if isinstance(input_buffer, ir.ReinterpretView):

                def unwrap_views(target) -> ir.Buffer:
                    if isinstance(target, ir.BaseView):
                        return unwrap_views(target.unwrap_view())
                    if isinstance(target, ir.MutableBox):
                        return unwrap_views(target.data)
                    assert isinstance(target, ir.Buffer), type(target)
                    return target

                input_buffer = unwrap_views(input_buffer)
            self.codegen_allocation(input_buffer)
            self.writeline(ReinterpretLine(self, input_buffer, buffer, layout))
            return

        if isinstance(layout, ir.CommBufferLayout):
            self.writeline(AllocateLine(self, buffer, comm_buffer=True))
            return

        self.writeline(AllocateLine(self, buffer))