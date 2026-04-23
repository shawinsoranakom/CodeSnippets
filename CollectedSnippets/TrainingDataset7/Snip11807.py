def get_prep_lookup(self):
        if isinstance(self.rhs, float):
            self.rhs = math.ceil(self.rhs)
        return super().get_prep_lookup()