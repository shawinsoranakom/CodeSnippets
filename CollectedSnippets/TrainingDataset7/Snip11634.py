def get_prep_lhs(self):
        if isinstance(self.lhs, (tuple, list)):
            return Tuple(*self.lhs)
        return super().get_prep_lhs()