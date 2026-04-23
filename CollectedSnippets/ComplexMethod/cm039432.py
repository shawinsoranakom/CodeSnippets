def _check_interaction_cst(self, n_features):
        """Check and validation for interaction constraints."""
        if self.interaction_cst is None:
            return None

        if self.interaction_cst == "no_interactions":
            interaction_cst = [[i] for i in range(n_features)]
        elif self.interaction_cst == "pairwise":
            interaction_cst = itertools.combinations(range(n_features), 2)
        else:
            interaction_cst = self.interaction_cst

        try:
            constraints = [set(group) for group in interaction_cst]
        except TypeError:
            raise ValueError(
                "Interaction constraints must be a sequence of tuples or lists, got:"
                f" {self.interaction_cst!r}."
            )

        for group in constraints:
            for x in group:
                if not (isinstance(x, Integral) and 0 <= x < n_features):
                    raise ValueError(
                        "Interaction constraints must consist of integer indices in"
                        f" [0, n_features - 1] = [0, {n_features - 1}], specifying the"
                        " position of features, got invalid indices:"
                        f" {group!r}"
                    )

        # Add all not listed features as own group by default.
        rest = set(range(n_features)) - set().union(*constraints)
        if len(rest) > 0:
            constraints.append(rest)

        return constraints