def merge(self, other: "Stack", out: CWriter) -> None:
        if len(self.variables) != len(other.variables):
            raise StackError("Cannot merge stacks: differing variables")
        for self_var, other_var in zip(self.variables, other.variables):
            if self_var.name != other_var.name:
                raise StackError(f"Mismatched variables on stack: {self_var.name} and {other_var.name}")
            self_var.in_local = self_var.in_local and other_var.in_local
            if other_var.memory_offset is None:
                self_var.memory_offset = None
        self.align(other, out)
        for self_var, other_var in zip(self.variables, other.variables):
            if self_var.memory_offset is not None:
                if self_var.memory_offset != other_var.memory_offset:
                    raise StackError(f"Mismatched stack depths for {self_var.name}: {self_var.memory_offset} and {other_var.memory_offset}")
            elif other_var.memory_offset is None:
                self_var.memory_offset = None