def lowest_latency(
        self,
        top: int = 1,
        verbose: bool = False,
        tier: int | None = None,
        attempts: int = 1,
    ) -> list[tuple[str, float, float, float, float]]:
        """Determine the GCP regions with the lowest latency based on ping tests.

        Args:
            top (int, optional): Number of top regions to return.
            verbose (bool, optional): If True, prints detailed latency information for all tested regions.
            tier (int | None, optional): Filter regions by tier (1 or 2). If None, all regions are tested.
            attempts (int, optional): Number of ping attempts per region.

        Returns:
            (list[tuple[str, float, float, float, float]]): List of tuples containing region information and latency
                statistics. Each tuple contains (region, mean_latency, std_dev, min_latency, max_latency).

        Examples:
            >>> regions = GCPRegions()
            >>> results = regions.lowest_latency(top=3, verbose=True, tier=1, attempts=2)
            >>> print(results[0][0])  # Print the name of the lowest latency region
        """
        if verbose:
            print(f"Testing GCP regions for latency (with {attempts} {'retry' if attempts == 1 else 'attempts'})...")

        regions_to_test = [k for k, v in self.regions.items() if v[0] == tier] if tier else list(self.regions.keys())
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            results = list(executor.map(lambda r: self._ping_region(r, attempts), regions_to_test))

        sorted_results = sorted(results, key=lambda x: x[1])

        if verbose:
            print(f"{'Region':<25} {'Location':<35} {'Tier':<5} Latency (ms)")
            for region, mean, std, min_, max_ in sorted_results:
                tier, city, country = self.regions[region]
                location = f"{city}, {country}"
                if mean == float("inf"):
                    print(f"{region:<25} {location:<35} {tier:<5} Timeout")
                else:
                    print(f"{region:<25} {location:<35} {tier:<5} {mean:.0f} ± {std:.0f} ({min_:.0f} - {max_:.0f})")
            print(f"\nLowest latency region{'s' if top > 1 else ''}:")
            for region, mean, std, min_, max_ in sorted_results[:top]:
                tier, city, country = self.regions[region]
                location = f"{city}, {country}"
                print(f"{region} ({location}, {mean:.0f} ± {std:.0f} ms ({min_:.0f} - {max_:.0f}))")

        return sorted_results[:top]