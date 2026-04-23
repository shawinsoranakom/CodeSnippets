def _set_factor_by_name(self, factor, name):
        error_msg = (
            f"The `{name}` argument should be a number "
            "(or a list of two numbers) "
            "in the range "
            f"[{self._FACTOR_BOUNDS[0]}, {self._FACTOR_BOUNDS[1]}]. "
            f"Received: factor={factor}"
        )
        if isinstance(factor, (tuple, list)):
            if len(factor) != 2:
                raise ValueError(error_msg)
            if (
                factor[0] > self._FACTOR_BOUNDS[1]
                or factor[1] < self._FACTOR_BOUNDS[0]
            ):
                raise ValueError(error_msg)
            lower, upper = sorted(factor)
        elif isinstance(factor, (int, float)):
            if (
                factor < self._FACTOR_BOUNDS[0]
                or factor > self._FACTOR_BOUNDS[1]
            ):
                raise ValueError(error_msg)
            factor = abs(factor)
            lower, upper = [max(-factor, self._FACTOR_BOUNDS[0]), factor]
        else:
            raise ValueError(error_msg)
        return lower, upper