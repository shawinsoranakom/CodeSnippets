def get_prep_lookup(self):
        rhs = self.rhs
        if isinstance(rhs, (tuple, list)) and len(rhs) == 1:
            rhs = rhs[0]
        if isinstance(rhs, bool):
            return rhs
        raise ValueError(
            "The QuerySet value for an isnull lookup must be True or False."
        )