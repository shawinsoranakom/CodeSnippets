def _generate_reuse(self, line: WrapperLine) -> None:
        assert isinstance(line, ReuseLine)
        old = line.node
        new = line.reused_as
        assert not any(buf.get_name() in V.graph.removed_buffers for buf in (old, new))
        assert old.get_dtype() == new.get_dtype()

        old_node = self.buffer_to_node[old.get_name()]
        result_node = old_node

        # Change shape and stride.
        size = tuple(new.get_size())
        stride = tuple(new.get_stride())
        offset = new.get_offset()
        if (
            tuple(old.get_size()) != size
            or tuple(old.get_stride()) != stride
            or old.get_offset() != offset
        ):
            result_node = self._create_as_strided(old_node, size, stride, offset)

        self._record_allocation(new, result_node)

        # Free the old buffer, if we allocated a new tensor.
        if (
            old.get_name() not in V.graph.get_output_names()
            and line.delete_old
            and result_node is not old_node
        ):
            self._free(old)