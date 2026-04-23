def __eq__(self, other):
        "Do equivalence testing on the features."
        return bool(capi.feature_equal(self.ptr, other._ptr))