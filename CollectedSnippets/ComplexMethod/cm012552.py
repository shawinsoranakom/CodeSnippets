def install_dims(self, var, dims, offset, is_store):
        """Try to set self.buffer_dimensions[var], return True on success"""
        if var not in self.buffer_dimensions:
            self.buffer_dimensions[var] = dims
            self.buffer_offsets[var] = offset
            return True
        if self.buffer_offsets[var] != offset or len(
            self.buffer_dimensions[var]
        ) != len(dims):
            return False
        if is_store:
            return self.buffer_dimensions[var] == dims
        for old, new in zip(self.buffer_dimensions[var], dims):
            if old.stride != new.stride:
                return False
            if old.size != new.size or old.expr != new.expr:
                old.size = V.graph.sizevars.evaluate_max(old.size, new.size)
                old.expr = None
        return True