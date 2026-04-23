def load_all(
        self,
        categories: Optional[list[str]] = None,
        skip_categories: Optional[list[str]] = None,
        names: Optional[list[str]] = None,
        maintain: bool = False,
        improve: bool = False,
        explore: bool = False,
    ) -> Iterator[Challenge]:
        """Load all challenges, optionally filtered by category or name.

        Args:
            categories: Only include challenges with at least one matching category.
            skip_categories: Exclude challenges with any matching category.
            names: Only include challenges with matching names.
            maintain: Only include regression tests (previously beaten consistently).
            improve: Only include non-regression tests (not consistently beaten).
            explore: Only include challenges never beaten.

        Yields:
            Challenge objects for each matching challenge.
        """
        for data_json in self.challenges_dir.rglob("data.json"):
            # Skip deprecated challenges
            if "deprecated" in str(data_json).lower():
                continue

            try:
                challenge = self._load_challenge(data_json)
            except Exception as e:
                # Skip malformed challenges
                print(f"Warning: Failed to load {data_json}: {e}")
                continue

            # Apply category filter (include)
            if categories:
                if not any(c in challenge.category for c in categories):
                    continue

            # Apply skip category filter (exclude)
            if skip_categories:
                if any(c in challenge.category for c in skip_categories):
                    continue

            # Apply name filter
            if names:
                if challenge.name not in names:
                    continue

            # Apply maintain/improve/explore filters
            if maintain or improve or explore:
                is_regression = self.is_regression_test(challenge.name)
                has_passed = self.has_been_passed(challenge.name)

                # --maintain: only challenges expected to pass (regression tests)
                if maintain and not is_regression:
                    continue

                # --improve: only challenges not consistently passed
                if improve and is_regression:
                    continue

                # --explore: only challenges never passed
                if explore and has_passed:
                    continue

            yield challenge