def pop(self, var: StackItem, out: CWriter) -> Local:
        if self.variables:
            top = self.variables[-1]
            if var.is_array() != top.is_array() or top.size != var.size:
                # Mismatch in variables
                self.clear(out)
        self.logical_sp = self.logical_sp.pop(var)
        indirect = "&" if var.is_array() else ""
        if self.variables:
            popped = self.variables.pop()
            assert var.is_array() == popped.is_array() and popped.size == var.size
            if not var.used:
                return popped
            if popped.name != var.name:
                rename = f"{var.name} = {popped.name};\n"
                popped.item = var
            else:
                rename = ""
            if not popped.in_local:
                if popped.memory_offset is None:
                    popped.memory_offset = self.logical_sp
                assert popped.memory_offset == self.logical_sp, (popped, self.as_comment())
                offset = popped.memory_offset - self.physical_sp
                if var.is_array():
                    defn = f"{var.name} = &stack_pointer[{offset.to_c()}];\n"
                else:
                    defn = f"{var.name} = stack_pointer[{offset.to_c()}];\n"
                    popped.in_local = True
            else:
                defn = rename
            out.emit(defn)
            return popped
        self.base_offset = self.logical_sp
        if var.name in UNUSED or not var.used:
            return Local.unused(var, self.base_offset)
        c_offset = (self.base_offset - self.physical_sp).to_c()
        assign = f"{var.name} = {indirect}stack_pointer[{c_offset}];\n"
        out.emit(assign)
        self._print(out)
        return Local.from_memory(var, self.base_offset)