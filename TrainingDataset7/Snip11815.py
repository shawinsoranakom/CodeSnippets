def is_simple_lookup(self):
        # A "simple lookup" is a Python value (as long as it's not a bilateral
        # transform).
        return self.rhs_is_direct_value() and not self.bilateral_transforms