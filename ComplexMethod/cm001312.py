def load_challenges(self) -> Iterator[Challenge]:
        """Load challenges from the SWE-bench dataset.

        Yields:
            Challenge objects for each SWE-bench instance.
        """
        self.ensure_setup()

        if self._dataset is None:
            return

        count = 0
        for item in self._dataset:
            # Apply repo filter (if subset is a repo name)
            if self.subset and self.subset not in ("full", "lite", "verified"):
                if item.get("repo") != self.subset:
                    continue

            # Apply limit
            if self.limit and count >= self.limit:
                break

            challenge = self._convert_to_challenge(item)
            yield challenge
            count += 1