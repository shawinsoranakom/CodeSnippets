def _clean_bound_field(self, bf):
        value = bf.initial if self.disabled else bf.data
        return self.clean(value)