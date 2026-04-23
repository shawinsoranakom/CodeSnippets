def include_run(self, run: Run) -> bool:
        """Check if a `Run` should be included in the log.

        Args:
            run: The `Run` to check.

        Returns:
            `True` if the `Run` should be included, `False` otherwise.
        """
        if run.id == self.root_id:
            return False

        run_tags = run.tags or []

        if (
            self.include_names is None
            and self.include_types is None
            and self.include_tags is None
        ):
            include = True
        else:
            include = False

        if self.include_names is not None:
            include = include or run.name in self.include_names
        if self.include_types is not None:
            include = include or run.run_type in self.include_types
        if self.include_tags is not None:
            include = include or any(tag in self.include_tags for tag in run_tags)

        if self.exclude_names is not None:
            include = include and run.name not in self.exclude_names
        if self.exclude_types is not None:
            include = include and run.run_type not in self.exclude_types
        if self.exclude_tags is not None:
            include = include and all(tag not in self.exclude_tags for tag in run_tags)

        return include