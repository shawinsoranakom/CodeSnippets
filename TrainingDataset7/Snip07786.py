def get_prep_lookup(self):
        from .expressions import ArraySubquery

        if isinstance(self.rhs, Query):
            self.rhs = ArraySubquery(self.rhs)
        return super().get_prep_lookup()