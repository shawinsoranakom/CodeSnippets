def __init__(self, param_grid):
        if not isinstance(param_grid, (Mapping, Iterable)):
            raise TypeError(
                f"Parameter grid should be a dict or a list, got: {param_grid!r} of"
                f" type {type(param_grid).__name__}"
            )

        if isinstance(param_grid, Mapping):
            # wrap dictionary in a singleton list to support either dict
            # or list of dicts
            param_grid = [param_grid]

        # check if all entries are dictionaries of lists
        for grid in param_grid:
            if not isinstance(grid, dict):
                raise TypeError(f"Parameter grid is not a dict ({grid!r})")
            for key, value in grid.items():
                if isinstance(value, np.ndarray) and value.ndim > 1:
                    raise ValueError(
                        f"Parameter array for {key!r} should be one-dimensional, got:"
                        f" {value!r} with shape {value.shape}"
                    )
                if isinstance(value, str) or not isinstance(
                    value, (np.ndarray, Sequence)
                ):
                    raise TypeError(
                        f"Parameter grid for parameter {key!r} needs to be a list or a"
                        f" numpy array, but got {value!r} (of type "
                        f"{type(value).__name__}) instead. Single values "
                        "need to be wrapped in a list with one element."
                    )
                if len(value) == 0:
                    raise ValueError(
                        f"Parameter grid for parameter {key!r} need "
                        f"to be a non-empty sequence, got: {value!r}"
                    )

        self.param_grid = param_grid