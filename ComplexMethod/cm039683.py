def __init__(self, param_distributions, n_iter, *, random_state=None):
        if not isinstance(param_distributions, (Mapping, Iterable)):
            raise TypeError(
                "Parameter distribution is not a dict or a list,"
                f" got: {param_distributions!r} of type "
                f"{type(param_distributions).__name__}"
            )

        if isinstance(param_distributions, Mapping):
            # wrap dictionary in a singleton list to support either dict
            # or list of dicts
            param_distributions = [param_distributions]

        for dist in param_distributions:
            if not isinstance(dist, dict):
                raise TypeError(
                    "Parameter distribution is not a dict ({!r})".format(dist)
                )
            for key in dist:
                if not isinstance(dist[key], Iterable) and not hasattr(
                    dist[key], "rvs"
                ):
                    raise TypeError(
                        f"Parameter grid for parameter {key!r} is not iterable "
                        f"or a distribution (value={dist[key]})"
                    )
        self.n_iter = n_iter
        self.random_state = random_state
        self.param_distributions = param_distributions