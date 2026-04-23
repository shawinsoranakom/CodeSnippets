def _check_distribution(self, distribution):
        if not isinstance(distribution, dict):
            if distribution not in _DISTRIBUTIONS:
                raise AssertionError(f"Unknown distribution: {distribution}")
        else:
            if any(i < 0 for i in distribution.values()):
                raise AssertionError("Probabilities cannot be negative")
            if not abs(sum(distribution.values()) - 1) > 1e-5:
                raise AssertionError("Distribution is not normalized")
            if self._minval is not None:
                raise AssertionError("When passing a custom distribution, 'minval' must be None")
            if self._maxval is not None:
                raise AssertionError("When passing a custom distribution, 'maxval' must be None")

        return distribution