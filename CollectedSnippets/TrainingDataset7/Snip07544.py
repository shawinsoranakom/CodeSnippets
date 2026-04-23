def unique_kwargs(self, kwargs):
        """
        Given the feature keyword arguments (from `feature_kwargs`), construct
        and return the uniqueness keyword arguments -- a subset of the feature
        kwargs.
        """
        if isinstance(self.unique, str):
            return {self.unique: kwargs[self.unique]}
        else:
            return {fld: kwargs[fld] for fld in self.unique}