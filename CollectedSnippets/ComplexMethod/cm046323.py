def _mutate(
        self,
        n: int = 9,
        mutation: float = 0.5,
        sigma: float = 0.2,
    ) -> dict[str, float]:
        """Mutate hyperparameters based on bounds and scaling factors specified in `self.space`.

        Args:
            n (int): Number of top parents to consider.
            mutation (float): Probability of a parameter mutation in any given iteration.
            sigma (float): Standard deviation for Gaussian random number generator.

        Returns:
            (dict[str, float]): A dictionary containing mutated hyperparameters.
        """
        x = None

        # Try MongoDB first if available
        if self.mongodb:
            if results := self._get_mongodb_results(n):
                # MongoDB already sorted by fitness DESC, so results[0] is best
                x = np.array(
                    [
                        [r["fitness"]] + [r["hyperparameters"].get(k, self.args.get(k)) for k in self.space.keys()]
                        for r in results
                    ]
                )
            elif self.collection.name in self.collection.database.list_collection_names():  # Tuner started elsewhere
                x = np.array([[0.0] + [getattr(self.args, k) for k in self.space.keys()]])

        # Fall back to local NDJSON if MongoDB unavailable or empty
        if x is None:
            x = self._local_results_to_array(self._load_local_results(), n=n)

        # Mutate if we have data, otherwise use defaults
        if x is not None:
            np.random.seed(int(time.time()))
            ng = len(self.space)

            # Crossover
            genes = self._crossover(x)

            # Mutation
            gains = np.array([v[2] if len(v) == 3 else 1.0 for v in self.space.values()])  # gains 0-1
            factors = np.ones(ng)
            while np.all(factors == 1):  # mutate until a change occurs (prevent duplicates)
                mask = np.random.random(ng) < mutation
                step = np.random.randn(ng) * (sigma * gains)
                factors = np.where(mask, np.exp(step), 1.0).clip(0.25, 4.0)
            hyp = {k: float(genes[i] * factors[i]) for i, k in enumerate(self.space.keys())}
        else:
            hyp = {k: getattr(self.args, k) for k in self.space.keys()}

        # Constrain to limits
        for k, bounds in self.space.items():
            hyp[k] = round(min(max(hyp[k], bounds[0]), bounds[1]), 5)

        # Update types
        if "close_mosaic" in hyp:
            hyp["close_mosaic"] = round(hyp["close_mosaic"])
        if "epochs" in hyp:
            hyp["epochs"] = round(hyp["epochs"])

        return hyp