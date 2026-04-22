def root_container(self) -> int:
        """The top-level container this cursor lives within - either
        RootContainer.MAIN or RootContainer.SIDEBAR."""
        raise NotImplementedError()