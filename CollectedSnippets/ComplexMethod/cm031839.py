def merge(self, other: "Storage", out: CWriter) -> None:
        self.sanity_check()
        if len(self.inputs) != len(other.inputs):
            self.clear_dead_inputs()
            other.clear_dead_inputs()
        if len(self.inputs) != len(other.inputs) and self.check_liveness:
            diff = self.inputs[-1] if len(self.inputs) > len(other.inputs) else other.inputs[-1]
            self._print(out)
            other._print(out)
            raise StackError(f"Unmergeable inputs. Differing state of '{diff.name}'")
        for var, other_var in zip(self.inputs, other.inputs):
            if var.in_local != other_var.in_local:
                raise StackError(f"'{var.name}' is cleared on some paths, but not all")
        if len(self.outputs) != len(other.outputs):
            self._push_defined_outputs()
            other._push_defined_outputs()
        if len(self.outputs) != len(other.outputs):
            var = self.outputs[0] if len(self.outputs) > len(other.outputs) else other.outputs[0]
            raise StackError(f"'{var.name}' is set on some paths, but not all")
        for var, other_var in zip(self.outputs, other.outputs):
            if var.memory_offset is None:
                other_var.memory_offset = None
            elif other_var.memory_offset is None:
                var.memory_offset = None
        self.stack.merge(other.stack, out)
        self.sanity_check()