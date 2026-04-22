def is_valid(self) -> bool:
        """True if there's a git repo here, and git.version >= MIN_GIT_VERSION."""
        return (
            self.repo is not None
            and self.git_version is not None
            and self.git_version >= MIN_GIT_VERSION
        )