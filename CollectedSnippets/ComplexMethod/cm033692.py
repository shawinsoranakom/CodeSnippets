def skip(
        self,
        skip: str,
        reason: str,
        targets: list[IntegrationTarget],
        exclude: set[str],
        override: t.Optional[list[str]] = None,
    ) -> None:
        """Apply the specified skip rule to the given targets by updating the provided exclude list."""
        if skip.startswith('skip/'):
            skipped = [target.name for target in targets if skip in target.skips and (not override or target.name not in override)]
        else:
            skipped = [target.name for target in targets if f'{skip}/' in target.aliases and (not override or target.name not in override)]

        self.apply_skip(f'"{skip}"', reason, skipped, exclude)