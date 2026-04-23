def make_buffer_reuse(self, old: BufferLike, new: BufferLike, delete_old: bool):
        assert old.get_dtype() == new.get_dtype()
        old_name = old.get_name()
        new_name = new.get_name()
        del_line = ";"
        if old_name not in V.graph.get_output_names() and delete_old:
            del_line = f"; {self.make_buffer_free(old)}"

        if old.get_size() == new.get_size() and old.get_stride() == new.get_stride():
            if old_name in self.stack_allocated_buffers:
                self.stack_allocated_buffers[new_name] = new
            return self.codegen_exact_buffer_reuse(old_name, new_name, del_line)

        reinterpret_view = self.codegen_reinterpret_view(
            old, new.get_size(), new.get_stride(), 0, self.wrapper_call.writeline
        )
        if reinterpret_view in self.stack_allocated_buffers:
            self.stack_allocated_buffers[new_name] = new
            # The only way to get into this case is via an exact buffer reuse, since all
            # other options result in a new tensor handle.
            return self.codegen_exact_buffer_reuse(old_name, new_name, del_line)
        return f"{self.declare}{new_name} = {reinterpret_view}{del_line}  // reuse"