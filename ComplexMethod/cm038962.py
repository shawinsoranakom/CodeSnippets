def __init__(
        self,
        mean: float | None = None,
        sigma: float | None = None,
        average: int | None = None,
        median_ratio: float | None = None,
        max_val: int | None = None,
    ) -> None:
        self.average = average
        self.median_ratio = median_ratio
        self.max_val = max_val

        if average is not None:
            if average < 1:
                raise ValueError("Lognormal average must be positive")

            if mean or sigma:
                raise ValueError(
                    "When using lognormal average, you can't provide mean/sigma"
                )

            if self.median_ratio is None:
                # Default value that provides relatively wide range of values
                self.median_ratio = 0.85

            # Calculate mean/sigma of np.random.lognormal based on the average
            mean, sigma = self._generate_lognormal_by_median(
                target_average=self.average, median_ratio=self.median_ratio
            )
        else:
            if mean is None or sigma is None:
                raise ValueError(
                    "Must provide both mean and sigma if average is not used"
                )

            if mean <= 0 or sigma < 0:
                raise ValueError(
                    "Lognormal mean must be positive and sigma must be non-negative"
                )

        # Mean and standard deviation of the underlying normal distribution
        # Based on numpy.random.lognormal
        self.mean = mean
        self.sigma = sigma